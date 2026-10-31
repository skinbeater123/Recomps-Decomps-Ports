void mcpx_apu_soft_reset(void)
{
    MCPXAPUState *d = g_state;

    if (!d)
        return;
    qemu_mutex_lock(&d->lock);
    mcpx_apu_reset_locked(d);
    qemu_mutex_unlock(&d->lock);
}
