import psycopg2

# Conectare la baza de date PostgreSQL
conn = psycopg2.connect(
    host="localhost", #baza de date rulează pe laptopul tău (nu pe internet)
    port="5432", #portul pe care l-am „legat" mai devreme, la pornirea containerului
    database="postgres", #numele bazei de date implicite (Postgres creează automat una cu acest nume)
    user="postgres", #utilizatorul implicit
    password="parola123" #parola pe care ai setat-o la pornirea containerului
)

cursor = conn.cursor()

# # Creăm un tabel simplu, "clienti"
# cursor.execute("""
#     CREATE TABLE clienti (
#         id SERIAL PRIMARY KEY,
#         nume VARCHAR(100),
#         status VARCHAR(50),
#         numar_comenzi INTEGER
#     )
# """)


# cursor.execute("""
#     INSERT INTO clienti (nume, status, numar_comenzi)
#     VALUES ('Ion Popescu', 'activ', 12)
# """)

# cursor.execute("""
#     INSERT INTO clienti (nume, status, numar_comenzi)
#     VALUES ('Maria Ionescu', 'inactiv', 3)
# """)

# cursor.execute("""
#     INSERT INTO clienti (nume, status, numar_comenzi)
#     VALUES ('Andrei Radu', 'activ', 25)
# """)

# conn.commit() # salvează schimbarea permanent în baza de date

# print("Date adăugate cu succes!")


# # Citim toți clienții din tabel
# cursor.execute("SELECT * FROM clienti")

# rezultate = cursor.fetchall()

# for rand in rezultate:
#     print(rand)

cursor.execute("SELECT * FROM clienti WHERE status = 'activ'")

rezultate = cursor.fetchall()

for rand in rezultate:
    print(rand)

cursor.close()
conn.close()