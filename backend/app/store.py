"""Every read and write to the database lives here."""


class Store:
    def __init__(self, client):
        self.client = client

    def list_students(self) -> list[dict]:
        return self.client.table("students").select("id,name").order("name").execute().data

    def add_student(self, name: str) -> dict:
        row = self.client.table("students").insert({"name": name}).execute().data[0]
        return {"id": row["id"], "name": row["name"]}
