# 1.	Ver modulos de Python https://docs.python.org/3/py-modindex.html#
# 2.	datetime formats https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior
# 3.	Codigo de idiomas https://www.science.co.il/language/Locale-codes.php

# 4.	para definir funciones 
def function ():
	try:
		pass
	except TypeError:
		pass
	except ZeroDivisionError:
		pass
	else:
		#return
		pass 

#5. Para abrir ficheros desde scripts
	# from io import open
text = "Prueba dos"
#file = open("file.txt","r")
with open("file.txt","r") as file:
	for line in file:
		print(line)
file.close()