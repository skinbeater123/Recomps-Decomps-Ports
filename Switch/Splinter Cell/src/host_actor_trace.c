/* Opt-in observation of the original script Move entry, with no guest changes. */
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <windows.h>
extern ptrdiff_t xbox_GetMemoryOffset(void);
static uint32_t observed[32];
static unsigned observed_count;
static uint32_t watched_axis;
static uint32_t traced_player, traced_camera;
void sc1_trace_exec_move(uint32_t actor)
{
    static int enabled = -1;
    static unsigned count;
    if (enabled < 0) enabled = getenv("SC1_TRACE_EXEC_MOVE") != NULL;
    if (!enabled) return;
    if (++count > 200 && (count % 1000)) return;
    if (actor < 0x10000u || actor > 0x03fffe00u) {
        fprintf(stderr, "[ACTOR] execMove #%u t=%llu actor=%08X (unmapped)\n", count, (unsigned long long)GetTickCount64(), actor);
        return;
    }
    unsigned i;
    for (i = 0; i < observed_count && observed[i] != actor; ++i) {}
    if (i == observed_count && observed_count < 32) observed[observed_count++] = actor;
    const uint32_t *object = (const uint32_t *)((const uint8_t *)xbox_GetMemoryOffset() + actor);
    fprintf(stderr, "[ACTOR] execMove #%u t=%llu actor=%08X words", count, (unsigned long long)GetTickCount64(), actor);
    for (unsigned i = 0; i < 64; ++i) fprintf(stderr, " %08X", object[i]);
    fputc('\n', stderr);
}

void sc1_trace_actor_snapshot(void)
{
    if (!getenv("SC1_TRACE_EXEC_MOVE")) return;
    for (unsigned n = 0; n < observed_count; ++n) {
        uint32_t actor = observed[n];
        const uint32_t *object = (const uint32_t *)((const uint8_t *)xbox_GetMemoryOffset() + actor);
        fprintf(stderr, "[ACTOR-SNAPSHOT] t=%llu actor=%08X words", (unsigned long long)GetTickCount64(), actor);
        for (unsigned i = 0; i < 64; ++i) fprintf(stderr, " %08X", object[i]);
        fputc('\n', stderr);
    }
}

void sc1_trace_xid_callback(uint32_t target, uint32_t object)
{
    static int enabled = -1;
    static uint32_t last_target, last_object;
    if (enabled < 0) enabled = getenv("SC1_TRACE_GUEST_PAD") != NULL;
    if (enabled && (target != last_target || object != last_object)) {
        last_target = target; last_object = object;
        fprintf(stderr, "[SC1-PAD] original callback target=%08X object=%08X call=0025C9D3\n", target, object);
    }
}

void sc1_trace_axis_stage(uint32_t key, uint32_t value, uint32_t stage, uint32_t detail, uint32_t object)
{
    static int enabled = -1;
    static uint32_t seen;
    unsigned bit;
    if (enabled < 0) enabled = getenv("SC1_TRACE_GUEST_PAD") != NULL;
    if (!enabled || key != 0xe1u || (value & 0x7fffffffu) == 0) return;
    bit = stage == 0x85a92u ? 1u : stage == 0x85aa7u ? 2u : stage == 0x85b6fu ? 4u : 8u;
    if (seen & bit) return;
    seen |= bit;
    fprintf(stderr, "[SC1-AXIS] key=%02X value=%08X stage=%08X detail=%08X input=%08X\n", key, value, stage, detail, object);
}

void sc1_trace_axis_exec(uint32_t target, uint32_t object, uint32_t command)
{
    static int enabled = -1;
    static unsigned seen;
    if (enabled < 0) enabled = getenv("SC1_TRACE_GUEST_PAD") != NULL;
    if (!enabled || seen >= 15 || object < 0x10000u || object > 0x03fff000u ||
        command < 0x10000u || command > 0x03ffff00u) return;
    const uint8_t *mem = (const uint8_t *)xbox_GetMemoryOffset();
    uint32_t state = *(const uint32_t *)(mem + object + 0xec8u);
    uint32_t value = *(const uint32_t *)(mem + object + 0xeccu);
    if (state != 2u || (value & 0x7fffffffu) == 0) return;
    const uint16_t *text = (const uint16_t *)(mem + command);
    char ascii[80]; unsigned i;
    for (i = 0; i < sizeof ascii - 1 && text[i] && text[i] < 128; ++i) ascii[i] = (char)text[i];
    ascii[i] = 0; ++seen;
    uint32_t viewport = *(const uint32_t *)(mem + object + 0xea4u), controller = 0;
    unsigned flags = 0xffffffffu;
    if (viewport >= 0x10000u && viewport < 0x03ffffc0u) {
        controller = *(const uint32_t *)(mem + viewport + 0x34u);
        if (controller >= 0x10000u && controller < 0x03fffc00u)
            flags = mem[controller + 0x380u];
    }
    fprintf(stderr, "[SC1-AXIS-EXEC] target=%08X state=%u value=%08X viewport=%08X controller=%08X flags380=%X command=%s\n", target, state, value, viewport, controller, flags, ascii);
}

void sc1_trace_axis_write(uint32_t stage, uint32_t property, uint32_t value)
{
    static unsigned count;
    static int watched;
    static uint32_t last_property, last_value;
    if (!getenv("SC1_TRACE_GUEST_PAD") || count >= 100) return;
    if (!watched && (value & 0x7fffffffu) && getenv("SC1_WATCH_AXIS_PROPERTY")) {
        extern int sc1_watch_address(uint32_t);
        watched = sc1_watch_address(property);
        if (watched) watched_axis = property;
    }
    if (!(value & 0x7fffffffu) && count >= 8) return;
    if (property == last_property && value == last_value) return;
    last_property = property; last_value = value; ++count;
    fprintf(stderr, "[SC1-AXIS-WRITE] stage=%08X property=%08X value=%08X\n",
            stage, property, value);
}

void sc1_trace_axis_constant(uint32_t frame, uint32_t result)
{
    static unsigned count;
    if (!watched_axis || result != watched_axis || count++ >= 8 ||
        frame < 0x10000u || frame > 0x03ffffe0u) return;
    const uint8_t *mem = (const uint8_t *)xbox_GetMemoryOffset();
    for (unsigned depth = 0; depth < 8 && frame >= 0x10000u && frame <= 0x03ffffe0u; ++depth) {
        const uint32_t *f = (const uint32_t *)(mem + frame);
        uint32_t node = f[1];
        if (node < 0x10000u || node >= 0x03ffffdcu) break;
        uint32_t name = *(const uint32_t *)(mem + node + 0x20);
        fprintf(stderr, "[SC1-AXIS-SCRIPT] depth=%u frame=%08X node=%08X name=%08X object=%08X code=%08X previous=%08X\n",
                depth, frame, node, name, f[2], f[3], f[5]);
        frame = f[5];
    }
}

void sc1_trace_input_gate(uint32_t frame, uint32_t property, uint32_t target, uint32_t value)
{
    static unsigned count;
    if (!getenv("SC1_TRACE_GUEST_PAD") || count >= 32 ||
        property < 0x10000u || property > 0x03ffffa8u ||
        frame < 0x10000u || frame > 0x03ffffe0u) return;
    const uint8_t *mem = (const uint8_t *)xbox_GetMemoryOffset();
    if (*(const uint16_t *)(mem + property + 0x44) != 0x380u ||
        *(const uint32_t *)(mem + property + 0x54) != 0x20u) return;
    ++count;
    const uint32_t *f = (const uint32_t *)(mem + frame);
    fprintf(stderr, "[SC1-INPUT-GATE] target=%08X flags=%08X node=%08X object=%08X code=%08X\n",
            target, value, f[1], f[2], f[3]);
}

static void sc1_trace_pattern_impl(uint32_t object, uint32_t frame, uint32_t called)
{
    static unsigned count;
    static struct { uint32_t object,node,flags; } seen[500];
    if (!getenv("SC1_TRACE_PATTERNS") || count >= 500 || object < 0x10000u ||
        object > 0x03fff000u || frame < 0x10000u || frame > 0x03ffffe0u) return;
    const uint8_t *mem = (const uint8_t *)xbox_GetMemoryOffset();
    uint32_t text = *(const uint32_t *)(mem + object + 0x28);
    if (text < 0x10000u || text > 0x03ffff00u) return;
    const uint16_t *s = (const uint16_t *)(mem + text);
    const uint32_t *f = (const uint32_t *)(mem + frame);
    uint32_t node = called ? called : f[1];
    if (node < 0x10000u || node > 0x03ffffd0u) return;
    uint32_t nt = *(const uint32_t *)(mem + node + 0x28);
    if (nt < 0x10000u || nt > 0x03ffff00u) return;
    char oname[100], fname[100]; unsigned i;
    for (i=0;i<99 && s[i] && s[i]<128;++i) oname[i]=(char)s[i]; oname[i]=0;
    s=(const uint16_t *)(mem+nt);
    for (i=0;i<99 && s[i] && s[i]<128;++i) fname[i]=(char)s[i]; fname[i]=0;
    if (!strcmp(oname,"EPlayerController0")) traced_player=object;
    if (!strcmp(oname,"EPlayerCam0")) traced_camera=object;
    if (!strcmp(fname,"GetPause")) return;
    if (!strncmp(oname,"ELambert",8) && (!strcmp(fname,"RotateTowardsRotator") || !strcmp(fname,"SetRotation"))) {
        static unsigned rotate_calls;
        if(rotate_calls++<12) fprintf(stderr,"[SC1-ROTATE] %s function=%s params=%08X yaw=%u\n",oname,fname,f[4],*(const uint32_t *)(mem+object+0xd4));
    }
    if (!(oname[0]=='P' && oname[1]=='_')) {
        if (!strncmp(oname,"EAIController",13)) {
            if (!strstr(fname,"Goal") && !strstr(fname,"State") && strcmp(fname,"Tick") && strcmp(fname,"GetTurnSpeed")) return;
        } else if (strncmp(oname,"EPlayerController",17) && strncmp(oname,"EPlayerCam",10)) return;
        if (!strstr(fname,"Cinematic") && !strstr(fname,"Pattern") &&
            !strstr(fname,"Pause") && !strstr(fname,"Start") && !strstr(fname,"Key") &&
            !strstr(fname,"Goal") && !strstr(fname,"State") && strcmp(fname,"Tick") && strcmp(fname,"GetTurnSpeed")) return;
    }
    uint32_t flags=*(const uint32_t *)(mem+object+0x2ec);
    for (i=0;i<count;++i)
        if (seen[i].object==object && seen[i].node==node && seen[i].flags==flags) return;
    seen[count].object=object;seen[count].node=node;seen[count].flags=flags;++count;
    fprintf(stderr,"[SC1-PATTERN] %s@%08X function=%s code=%08X flags=%08X locals=%08X\n",
            oname,object,fname,f[3],*(const uint32_t *)(mem+object+0x2ec),f[4]);
}
void sc1_trace_pattern_call(uint32_t object, uint32_t frame) { sc1_trace_pattern_impl(object,frame,0); }
void sc1_trace_pattern_invoke(uint32_t object, uint32_t frame, uint32_t node) { sc1_trace_pattern_impl(object,frame,node); }

void sc1_trace_ai_goal(uint32_t stage, uint32_t object, uint32_t goal, uint32_t result)
{
    static unsigned counts[32];
    static uint32_t heads[32];
    if (!getenv("SC1_TRACE_PATTERNS") || stage>=32 ||
        object<0x10000u || object>0x03fff000u) return;
    const uint8_t *m=(const uint8_t *)xbox_GetMemoryOffset();
    uint32_t t=*(const uint32_t *)(m+object+0x28);
    if(t<0x10000u || t>0x03ffff00u) return;
    const uint16_t *s=(const uint16_t *)(m+t);
    char name[80]; unsigned i;
    for(i=0;i<79 && s[i] && s[i]<128;++i)name[i]=(char)s[i];name[i]=0;
    if(strcmp(name,"EAIController0"))return;
    if(stage==0){
        static ULONGLONG last;
        ULONGLONG now=GetTickCount64();
        if(!last || now-last>=1000){
            last=now;
            uint32_t pawn=*(const uint32_t*)(m+object+0x37c);
            uint32_t sam=traced_player?*(const uint32_t*)(m+traced_player+0x288):0;
            if(pawn>=0x10000u && pawn<0x03fff000u){
                const float*p=(const float*)(m+pawn+0xc4);
                fprintf(stderr,"[SC1-WORLD] Lambert=%g,%g,%g yaw=%u",p[0],p[1],p[2],*(const uint32_t*)(m+pawn+0xd4));
                if(sam>=0x10000u && sam<0x03fff000u){
                    p=(const float*)(m+sam+0xc4);
                    fprintf(stderr," Sam=%g,%g,%g yaw=%u stop=%u cinematic=%u",p[0],p[1],p[2],*(const uint32_t*)(m+sam+0xd4),!!(m[traced_player+0x380]&0x20),m[traced_player+0x5e0]&1);
                }
                if(traced_camera){p=(const float*)(m+traced_camera+0xc4);fprintf(stderr," camera=%g,%g,%g",p[0],p[1],p[2]);}
                fputc('\n',stderr);
            }
        }
    }
    uint32_t list=*(const uint32_t *)(m+object+0x504);
    uint32_t head=list>=0x10000u && list<0x03fffd00u?*(const uint32_t *)(m+list+0x288):0;
    if (heads[stage]!=head) { heads[stage]=head; counts[stage]=0; }
    if(counts[stage]++>=5)return;
    fprintf(stderr,"[SC1-AI] stage=%u object=%08X goal=%08X head=%08X count=%u flags=%08X pawn=%08X result=%08X\n",
        stage,object,goal,head,counts[stage],*(const uint32_t *)(m+object+0x38c),*(const uint32_t *)(m+object+0x37c),result);
}

void sc1_trace_rotation(uint32_t stage,uint32_t pawn,uint32_t params,uint32_t result)
{
 static unsigned counts[8];
 if(!getenv("SC1_TRACE_PATTERNS") || stage>=8 || counts[stage]>=16 || pawn<0x10000u || pawn>0x03fff000u || params<0x10000u || params>0x03ffff00u)return;
 const uint8_t*m=(const uint8_t*)xbox_GetMemoryOffset();
 uint32_t t=*(const uint32_t*)(m+pawn+0x28);
 if(t<0x10000u || t>0x03ffff00u)return;
 const uint16_t*n=(const uint16_t*)(m+t);
 if(n[0]!='E'||n[1]!='L'||n[2]!='a')return;
 ++counts[stage];const uint32_t*p=(const uint32_t*)(m+params);
 fprintf(stderr,"[SC1-ROTATION] stage=%u yaw=%u result=%08X params=%08X,%08X,%08X,%08X,%08X\n",stage,*(const uint32_t*)(m+pawn+0xd4),result,p[0],p[1],p[2],p[3],p[4]);
}

void sc1_trace_turn_result(uint32_t stack,uint32_t result,uint32_t target)
{
 static unsigned count;
 if(!getenv("SC1_TRACE_PATTERNS") || count>=16 || stack<0x10000u || stack>0x03ffff00u)return;
 const uint32_t*p=(const uint32_t*)((const uint8_t*)xbox_GetMemoryOffset()+stack);
 if(p[2]!=32196)return;
 ++count;fprintf(stderr,"[SC1-TURN-RESULT] caller=%08X step=%08X current=%u targetreg=%u result=%u\n",p[0],p[1],p[2],target,result);
}

void sc1_trace_turn_store(uint32_t frame,uint32_t result,uint32_t value)
{
 static unsigned count;
 if(!getenv("SC1_TRACE_PATTERNS") || count>=16 || frame<0x10000u || frame>0x03ffff00u)return;
 const uint8_t*m=(const uint8_t*)xbox_GetMemoryOffset();const uint32_t*f=(const uint32_t*)(m+frame);
 if(value<32190 || value>32800)return;
 ++count;fprintf(stderr,"[SC1-TURN-STORE] object=%08X result=%08X value=%u locals=%08X newYaw=%u code=%08X\n",f[2],result,value,f[4],*(const uint32_t*)(m+f[4]+0x1c),f[3]);
}

void sc1_trace_rotate_let(uint32_t frame,uint32_t target,uint32_t stage)
{
 static unsigned count;
 if(!getenv("SC1_TRACE_PATTERNS") || count>=180 || frame<0x10000u || frame>0x03ffff00u)return;
 const uint8_t*m=(const uint8_t*)xbox_GetMemoryOffset();const uint32_t*f=(const uint32_t*)(m+frame);
 if(f[1]<0x10000u || f[1]>0x03ffff00u || f[4]<0x10000u || f[4]>0x03ffff00u)return;
 uint32_t t=*(const uint32_t*)(m+f[1]+0x28);
 if(t<0x10000u || t>0x03ffff00u)return;
 const uint16_t*n=(const uint16_t*)(m+t);
 if(n[0]!='R'||n[1]!='o'||n[2]!='t'||n[3]!='a')return;
 ++count;fprintf(stderr,"[SC1-ROTATE-LET] stage=%u target=%08X code=%08X locals=%08X newYaw=%u\n",stage,target,f[3],f[4],*(const uint32_t*)(m+f[4]+0x1c));
}
