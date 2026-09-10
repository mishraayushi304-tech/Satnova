from services.supabase_service import supabase


def save_chat(user_id, question, answer, image_path=None):

    data = {
        "user_id": user_id,
        "question": question,
        "answer": answer,
        "image_path": image_path
    }

    response = (
        supabase
        .table("chat_history")
        .insert(data)
        .execute()
    )

    return response.data

#get chat history

def get_chat_history(user_id):

    response = (
        supabase
        .table("chat_history")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    return response.data