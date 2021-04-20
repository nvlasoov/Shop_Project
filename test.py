from requests import get, post, delete

print(delete('http://localhost:5000/api/products/999').json())
# новости с id = 999 нет в базе

print(delete('http://localhost:5000/api/products/2').json())