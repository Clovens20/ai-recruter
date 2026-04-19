-- A executer seul dans Supabase > SQL si tu as deja cree les tables
-- mais que GET /rest/v1/leads renvoie encore 503 (PGRST002 dans les logs).

NOTIFY pgrst, 'reload schema';
