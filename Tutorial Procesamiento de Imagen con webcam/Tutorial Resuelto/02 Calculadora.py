#Título
print("                     ## CALCULADORA ##")
print("A continuación, ingrese las variables para calcular su suma, resta y multiplicación...")
# Calculadora, primero empezaremos pidiendo el primer número
print("\nIngrese el primer número: ")
# Guardaremos este número en la variable que llamaremos "a"
a = int(input())
# Pediremos el segundo número
print("Ingrese el segundo número: ")
# Guardaremos el nuevo número en la variable que llamaremos "b"
b = int(input())
# Ahora sumaremos estos dos números de la siguiente forma
# Utilizaremos una nueva variable "s" para guardar el resultado de esta
s= a + b
# Mostramos el resultado por pantalla
print(f"Valor de la suma: {s}")
# La resta queda parecida a la de la suma
r = a - b
# Muestra la resta
print(f"Valor de la resta es: {r}")
# Por último haremos lo mismo con la multiplicación
m = a * b
print(f"Valor de la multiplicación es: {m}")

print("\n                    ## División ##")
# Pedimos dos números nuevamente
print("\nIngrese el primer valor a dividir")
x = int(input())
print("Ingrese el segundo valor de la división (este valor no puede ser 0 >:c)")
y= int(input())

division = x / y
print(f"Valor de la división es: {division}")