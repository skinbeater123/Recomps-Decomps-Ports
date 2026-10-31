void xbox_rtl_soft_reset(void)
{
    AcquireSRWLockExclusive(&g_cs_table_lock);
    memset(g_cs_table, 0, sizeof(g_cs_table));
    g_cs_table_full = 0;
    ReleaseSRWLockExclusive(&g_cs_table_lock);
}
