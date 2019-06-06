##!/usr/bin/env python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        MyElGamal
# Purpose:     Implementación de algoritmo de firma digital de ElGamal sobre F_2
#
# Author:      ISC. Carlos Enrique Quijano Tapia
#
# Created:     05/11/2013
# Copyright:   (c) Kike 2013
# Licence:     GPLv3
#-------------------------------------------------------------------------------


import random
import Primos


def readFile(archivo):
	""" Lee un archivo y lo convierte en una cadena binaria """
	with open(archivo, mode='rb') as file:
		read = file.read()
		file.close()
	return read


def SHAfa(message):
	""" Digestor SHAfa """
	suma = [0,0]

	flag = True
	for text in message:
		if flag:
			suma[0] += text
		else:
			suma[1] += text
		flag = not flag

	suma[0] *= suma[1]
	suma[1] *= suma[0]

	suma[0] %= 256	# Corrección con respecto a C
	suma[1] %= 256	# Corrección con respecto a C

##	print(suma[1], suma[0])
	return 256 * suma[1] + suma[0]


def h(m):
	return SHAfa(m)


def fastExponentαTable(a, k, table):
	""" Exponenciación rápida """
	A = a
	bms = bitMoreSignificative(k) - 2

	while bms >= 0:
		# A ^ 2
		αPowA = fndPowα(table, A)
		A = table[(αPowA + αPowA) % len(table)][1]

		# Extraer bit
		if (k >> bms) & 0b1 == 1:
			# A * a
			αPowA = fndPowα(table, A)
			αPowa = fndPowα(table, a)
			A = table[(αPowA + αPowa) % len(table)][1]

		bms -= 1

	return A


def prodα(A, B, table):
	αPowA = fndPowα(table, A)
	αPowB = fndPowα(table, B)

	return table[(αPowA + αPowB) % len(table)][1]


def fndPowα(table, pol):
	result = None
	for i in table:
		if pol == i[1]:
			result = i[0]
	return result


def egcd(a, b):
	""" Encuentra el máximo comun divisor aplicando el algoritmo extendido de
	Euler.
	http://stackoverflow.com/questions/4798654/modular-multiplicative-inverse-function-in-python"""
	if a == 0:
		return (b, 0, 1)
	else:
		g, y, x = egcd(b % a, a)
		return (g, x - (b // a) * y, y)


def multiplicativeInverse(z, Zp):
	""" Encuentra z^-1 aplicando el algoritmo extendido de Euler """
	g, t, y = egcd(z, Zp)
	if g != 1:
		raise Exception('El  módulo inverso de %s en Z_%s, no existe' % (z, Zp))
	else:
		return t % Zp


def bitMoreSignificative(num):
	""" Obtiene el bit mas significativo de un numero binario """
	bms = 0
	while True:
		if 2 ** bms > num:
			break
		bms += 1
	return bms


def modPol_2(a, b):
	""" Operación módulo, para polinomios expresados como cadenas binarias """
	if a < b:
		return a
	else:
		# Obtenemos el bit más significativo
		if a > b:
			bms = bitMoreSignificative(a)
		else:
			bms = bitMoreSignificative(b)
		# Busca divisor
		for d in range(bms):
			bd = b << d
			r = a ^ bd
			# Sí divide (el residúo es menor que el divisor)
			if bd > r:
				# Vuelve a dividir el residuo
				return modPol_2(r, b)


def prodPol_2(a, b):
	""" Producto polinomal, para polinomios expresados como cadenas binarias """
	# Verificamos si podemos reducir operaciones intercambiando datos
	if a > b:
		tmp = a
		a = b
		b = tmp

	# Obtenemos el bit mas significativo
	bms = bitMoreSignificative(a)

	# Recorremos el la cadena binaria
	c = 0b0
	for slide in range(bms + 1):
		# Verificamos que el bit este encendido
		if (a >> slide) & 0b1 == 1:
			# Deslizamos y agregamos a c
			c ^= b << slide
	return c


def buildαTable_2(iPol, q, m):
	""" Genera tabla de potencias de α para campos finitos q^m """
	qm = q ** m
	bms = bitMoreSignificative(iPol)
	basis = modPol_2(iPol, 1 << bms - 1)
	bmsBasis = bitMoreSignificative(basis)
	table = []
	for α in range(qm - q + 1):
		if α < bms - 1:
			table.append((α, 1 << α))
		elif α == (bms - 1):
			table.append((α, basis))
		else:
			newα = prodPol_2(0b10, table[α - 1][1])
			newα = modPolαTable_2(table, newα)
			table.append((α, newα))
	return table


def modPolαTable_2(table, pol):
	""" Reemplaza los polinomios coeficientes de los polinomios binários, por
	los de la tabla """
	bms = bitMoreSignificative(pol)
	p = len(table)

	# Recorremos la cadena binaria
	result = 0b0
	for s in range(bms + 1):
		# Verificamos que el bit este encendido
		if (pol >> s) & 0b1 == 1:
			result ^= table[s % p][1]
	return result


class ELGAMAL(object):


	a = None


	def generateKeys(self, Zp, pol, table):
		""" Key generation for the ElGamal signature scheme """
		# SUMMARY: each entity creates a public key and corresponding private
		# key. Each entity A should do the following:
		self.table = table
		self.pol = pol
		# 1. Generate a large random prime p and a generator alpha of the
		# multiplicative group Z*_p (using Algorithm 4.84 Selecting a k-bit
		# prime p and a generator alpha of Z*_p).
		p = 2 ** 16
		α = 2

		# 2. Select a random integer a, 1 <= a <= p − 2.
		a = 12345
		self.a = a

		# 3. Compute y = alpha^a mod p (e.g., using Algorithm 2.143).
		y = fastExponentαTable(α, a, table)

		# 4. A’s public key is (p, alpha, y); A’s private key is "a".
		return p, α, y


	def sign(self, p, α, y, msg):
		""" Signature generation. Entity A should do the following """
		# (a) Select a random secret integer k, 1 <= k <= p − 2, with
		# gcd(k, p − 1) = 1.
		k = 11

		# (b) Compute r = alpha^k mod p (e.g., using Algorithm 2.143).
		r = fastExponentαTable(α, k, self.table)

		# (c) Compute k^{−1} mod (p − 1) (e.g., using Algorithm 2.142).
		invK = multiplicativeInverse(k, p - 1)

		# (d) Compute s = k^{−1}{h(msg) − a*r} mod (p − 1).
		s = (invK * (h(msg) - self.a * r) ) % (p - 1)

		# (e) A’s signature for msg is the pair (r, s).
		return r, s


	def verification(self, p, α, y, r, s, msg):
		""" Verification. To verify A’s signature (r, s) on msg, B should do the
		following: """
		# (a) Obtain A’s authentic public key (p, alpha, y).
		# (b) Verify that 1 <= r <= p − 1; if not, then reject the signature.
		if 1 <= r <= p -1:

			# (c) Compute v1 = y^r * r^s mod p.
			yr = fastExponentαTable(y, r, self.table)
			rs = fastExponentαTable(r, s, self.table)
			v1 = prodα(yr, rs, self.table)

			# (d) Compute h(msg) and v2 = alpha^{h(msg}} mod p.
			hm = h(msg)
			v2 = fastExponentαTable(α, hm, self.table)

			# (e) Accept the signature if and only if v1 = v2.

			print('y^r = %s\nr^s = %s\nv1 = %s\nv2 = %s' %
					(yr, rs, v1, v2,))

			if v1 == v2:
				print('\n\tQUEDA VERIFICADO')
				return True
			else:
				print('No Verificado')
				return False
		else:
			print('Firma rechazada')
			return False


def eval():
	##    65432109876543210
	π = 0b10010100001000001
	q = 2
	m = 16
	α = 2
	a = 12345
	k = 11
	qm = q ** m

	msg = readFile('Documento')
	table = buildαTable_2(π, q, m)
	egm = ELGAMAL()

	print('=' * 40)

	# Calcula el orden -> 2^16 -1
	result = fastExponentαTable(0b10, qm - 1, table)
	if result == 1:
		print('Comprobado que el orden es 2^16 - 1')
	else:
		print('El Orden no es 2^16 - 1, al elevarlo nos dio', result, bin(result))
##	result = α
##	order = 1
##	while True:
##		order += 1
##		result = prodα(result, α, table)
##		if result == 1:
##			break
##	print('Orden de %s es %s' % (α, order))

	# Obtener y = alpha^α
	print('\nGenerando llaves')
	p, α, y = egm.generateKeys(qm, π, table)
	print('y =', y)

	# Firmar doc r y s
	print('\nFirmando')
	r, s = egm.sign(p, α, y, msg)
	print('r =', r, '\ns =', s)

	# Encontrar r, s, y^r, r^s, v1 y v2
	print('\nVerificando')
	egm.verification(p, α, y, r, s, msg)


def main():
	for i in range(2):
		eval()
		print('')

if __name__ == '__main__':
    main()