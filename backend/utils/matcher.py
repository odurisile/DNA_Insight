
def match_variants(user, con):
    rsids = list(user.keys())
    placeholders = ",".join([f"'{r}'" for r in rsids])

    query = f'''
        SELECT *
        FROM nih_data
        WHERE rsid IN ({placeholders})
    '''

    results = con.execute(query).fetchall()
    columns = [c[0] for c in con.execute("DESCRIBE SELECT * FROM nih_data").fetchall()]

    output = []
    for row in results:
        item = {columns[i]: row[i] for i in range(len(columns))}
        item["user_genotype"] = user.get(item["rsid"], None)
        output.append(item)

    return output
