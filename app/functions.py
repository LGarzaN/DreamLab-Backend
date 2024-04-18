def get_requirements_query(reqs : str):
    query = "\n"
    arr = reqs.split(",")
    print(arr)

    for i in arr:
        arr2 = i.split("=")
        query += f"INSERT INTO [dbo].[UserRequirements] (GroupId, RequirementId, Quantity) VALUES (@GroupID, {arr2[0]}, {arr2[1]});\n"
    return query