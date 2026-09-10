from services.supabase_service import supabase

response = supabase.table("chat_history").select("*").execute()

print(response.data)
