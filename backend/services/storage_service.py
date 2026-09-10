from services.supabase_service import supabase


def upload_image(file_path: str, file_name: str):

    with open(file_path, "rb") as file:

        response = (
            supabase.storage
            .from_("sat-images")
            .upload(
                path=file_name,
                file=file,
                file_options={
                    "content-type": "image/jpeg"
                }
            )
        )

    return response