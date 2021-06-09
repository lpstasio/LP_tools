import re
import glob
import os

nome_programma     = 'PRTEST00'
nome_programmatore = 'DAVIDE'
utensili           = [['2', 'F6', '35']]
dima               = '6A'
n_robot            = '8'

info_text = '''
;                        __NOMEPR__
;
;  __UTENSILI__   DIMA __DIMA__      ROBOT __NROBOT__    __PROGRAMMATORE__
;
'''[1:]

start = '''
;
M24S19000                     <---- n motore
;
G79 G0 Z0
G90 G0 Y-100
;
(UIO,X,Y,Z)                   <---- dima
;
G90 G0 X Y B A                <---- primo g0 programma
;
L365=0
L385=35.00 ; L. ut. Libera
L386=4 ; Numero Motore        <---- n motore
;
(TCP,1)
;
N17 G90 G0 X Y                <---- primo g0 programma
;
'''[1:]

end = '''
;
(TCP)
;
(UAO,0)
;
G90 G0 Z0
G90 G0 Y-100
;
A0 B0
;
X0 Y0 Z0
;
M5
;
'''[1:]

def process(name):
	print("opening ", name)
	info_inserted = False


	# Preparazione info
	utensili_text = ''
	for ut in utensili:
		utensili_text += 'M{} {} L{} - '.format(ut[0], ut[1], ut[2])
	utensili_text = utensili_text[:-3]

	with open('in/' + name,'r') as fin:
		should_overwrite = True
		if os.path.exists('out/' + name):
			#choice = input("\nIl file '" + name + "' esiste nella cartella 'out', sovrascrivere? [Sn] ")
			#should_overwrite = choice[0].lower() == 's'
			should_overwrite = True
		if should_overwrite:
			with open('out/' + name, 'w') as fout:
				for line in fin.readlines():
					if (not info_inserted) and ('DIS' in line):       # Info iniziale
						fout.write(info_text.\
								   replace('__NOMEPR__', nome_programma).\
								   replace('__UTENSILI__', utensili_text).\
								   replace('__DIMA__', dima).\
								   replace('__NROBOT__', n_robot).\
								   replace('__PROGRAMMATORE__', nome_programmatore))
						info_inserted = True
					fout.write(line)

if __name__ == '__main__':
	paths = glob.glob('in/*.nc')
	if not os.path.exists('out'):
	    os.makedirs('out')

	for path in paths:
		filename = os.path.basename(path)
		if not ('maschera' in filename):
			process(filename)
	
	#input("\n\nPremere invio per chiudere...")

