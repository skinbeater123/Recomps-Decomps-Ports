"""Exercise CPU framebuffer / Vulkan-image ordering without retail data or a GPU."""
from pathlib import Path
import subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
TEST=r'''
#include <assert.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define VK_MAX_SURF 4
#define VK_IMAGE_ASPECT_COLOR_BIT 1
#define VK_IMAGE_LAYOUT_GENERAL 1
#define LOGE(...) ((void)0)
typedef size_t VkDeviceSize;
typedef struct { size_t bufferOffset; uint32_t bufferRowLength,bufferImageHeight;
 struct { uint32_t aspectMask,mipLevel,baseArrayLayer,layerCount; } imageSubresource;
 struct { int x,y,z; } imageOffset;
 struct { uint32_t width,height,depth; } imageExtent; } VkBufferImageCopy;
typedef struct {uint32_t va,w,h,pw,ph,used; int image,dirty; uint32_t gen;
 uint32_t sc1_pitch,sc1_bpp,sc1_cpu_hash,sc1_cpu_draw_frame; int sc1_cpu_known;} VkSurf;
static VkSurf s_surf[VK_MAX_SURF];
static uint8_t ram[4096], staging[4096], pixels[4096];
static int fail_ring,copies,s_drew_any,s_cb,barriers,pending;
static uint32_t crtc;
static struct {int ring;} frame;
/* Use the actual member access spelling expected by the runtime include. */
#undef s_f
#define s_f (&frame)
static ptrdiff_t xbox_GetMemoryOffset(void) {return (ptrdiff_t)ram;}
static uint32_t xbox_mmio_read(uint32_t va,unsigned size) {assert(va==0xFD600800u&&size==4);return crtc;}
static uint32_t bytes_hash_full(uint32_t va,uint32_t bytes) {
 uint32_t h=2166136261u;for(uint32_t i=0;i<bytes;i++)h=(h^ram[va+i])*16777619u;return h;
}
static size_t ring_alloc(uint32_t bytes,int align,void **ptr) {
 assert(bytes<=sizeof staging&&align==16);*ptr=fail_ring?NULL:staging;return 0;
}
static void pend_flush(void) {pending=0;}
static void end_rendering(void) {}
static void barrier_all(void) {barriers++;}
static void vkCmdCopyBufferToImage(int cb,int ring,int image,int layout,int count,const VkBufferImageCopy *c) {
 (void)cb;(void)ring;(void)image;assert(layout==1&&count==1&&pending==0&&barriers>0);
 for(uint32_t y=0;y<c->imageExtent.height;y++)
  memcpy(pixels+y*c->imageExtent.width*4,staging+c->bufferOffset+y*c->bufferRowLength*4,c->imageExtent.width*4);
 copies++;
}
#include "vk_scanout.inc"
int main(void) {
 VkSurf *s=&s_surf[0];*s=(VkSurf){.va=64,.w=2,.h=2,.pw=2,.ph=2,.image=1,.sc1_pitch=12,.sc1_bpp=4};
 sc1_surface_cpu_baseline(s);memset(pixels,0xEF,16);
 assert(!sc1_surface_cpu_sync(s)&&copies==0); /* a GPU clear survives stale RAM */
 ram[64]=0x12;ram[76]=0x34;pending=1;
 assert(sc1_surface_cpu_sync(s)&&pixels[0]==0x12&&pixels[8]==0x34&&copies==1&&s_drew_any);
 pixels[0]=0xA5; /* the original GPU progress overlay */
 assert(!sc1_surface_cpu_sync(s)&&pixels[0]==0xA5&&copies==1);
 ram[64]=0x56;fail_ring=1;assert(!sc1_surface_cpu_sync(s)&&pixels[0]==0xA5);
 fail_ring=0;assert(sc1_surface_cpu_sync(s)&&pixels[0]==0x56&&copies==2);
 ram[64]=0x78;sc1_surface_cpu_baseline(s);pixels[0]=0x11;
 assert(!sc1_surface_cpu_sync(s)&&pixels[0]==0x11); /* a subsequent original clear wins */
 ram[64]=0x9A;s->pw=4;assert(!sc1_surface_cpu_sync(s)&&pixels[0]==0x11);s->pw=2;
 VkSurf *other=&s_surf[1];*other=*s;other->va=128;other->sc1_cpu_known=0;
 ram[128]=0xBC;assert(sc1_surface_cpu_sync(other)&&pixels[0]==0xBC);
 assert(sc1_surface_cpu_sync(s)&&pixels[0]==0x9A); /* buffers keep separate RAM generations */
 crtc=128;assert(sc1_scanout_surface(s)==other);
 crtc=256;assert(sc1_scanout_surface(s)==s);
 other->va=0x80000040u;other->used=2;s->used=1;crtc=64;
 assert(sc1_scanout_surface(s)==other); /* physical scanout resolves a contiguous VA */
 return 0;
}
'''
with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
 p=Path(tmp);(p/'test.c').write_text(TEST)
 vs=Path(r'C:\Programming\VisualStudio\2026\Community')
 cmd=f'call "{vs / "Common7/Tools/VsDevCmd.bat"}" -arch=amd64 -host_arch=amd64 >nul && "{vs / "VC/Tools/Llvm/x64/bin/clang-cl.exe"}" /nologo /W3 /I"{ROOT / "src"}" "{p / "test.c"}" /Fe:"{p / "test.exe"}" && "{p / "test.exe"}"'
 (p/'test.cmd').write_text('@echo off\n'+cmd+'\n')
 subprocess.run(['cmd.exe','/c',str(p/'test.cmd')],cwd=p,check=True)
print('CPU framebuffer upload, overlay ordering and scanout selection checks passed')
