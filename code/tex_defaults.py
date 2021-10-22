NCSEC_MOTORE      = 0
NCSEC_UTENSILE    = 1
NCSEC_LUNGHEZZA   = 2
NCSEC_COORDINATES = 3
NCSEC_TOTAL       = 4
MOTORE_UTENSILE   = 0
MOTORE_LUNGHEZZA  = 1

MASCHERA_NOMASCHERA = ''
MASCHERA_BASE       = 'base'
MASCHERA_NUMERI     = 'numeri'
MASCHERA_25MM       = '25mm'
MASCHERA_15MM       = '15mm'


# @todo: move into config
SEARCH_L385  = 'L385'
SEARCH_L386  = 'L386'
SEARCH_FRESA = 'FRESA CILINDRICA'
SEARCH_DISCO = 'FRESA SFERICA'
MARK_SECTION_START = '(TCP,'
MARK_SECTION_END   = ['(TCP)', 'FINE PROGRAMMA']

X_INDEX = 0
Y_INDEX = 1
Z_INDEX = 2

default_vars = {
	'ORIGX'                          : '',
	'ORIGY'                          : '',
	'ORIGZ'                          : '',
	'VELOCITAROTAZIONEFRESA'         : '19000',

	'PROGRAMMA'                      : 'PRG0123',
	'CLIENTE'                        : 'cliente',
	'DESCRIZIONE_PRIMA_RIGA'         : 'Descrizione',
	'DESCRIZIONE_ALTRE_RIGHE'        : '',
	'CODICE'			             : '00.00.00.00',
	'UTENSILI'                       : 'UTENSILI',
	'ROBOT'                          : '',
	'REV'                            : '',
	'POSIZIONEDIMA'                  : 'XX',

	# @todo: maybe remove these
	'MASCHERA_TYPE'                  : MASCHERA_NOMASCHERA,
	'MASCHERA_DEPTH'                 : '',
}

default_config = {
	"stringa_cliente"                       : "CLIENTE",
	"stringa_descrizione_pezzo"             : "DESCRIZIONE PEZZO",
	"stringa_codice"                        : "CODICE PEZZO",
	"stringa_revisione"                     : "REV",
	"stringa_nome_programma"                : "NOTE",
	"descrizione_max_lunghezza_prima_riga"  : "0",
	"descrizione_max_lunghezza_altre_righe" : "0",
	"formato_data"                          : "g.m.aaaa",
	"righe_numerate"                        :  "1",
	"numerazione_righe_sulla_destra"        :  "1",
	"distanza_numeri_righe"                 :  "70",
	"mantieni_prima_coordinata"             :  "1",
	"ottimizza_link"                        :  "1",
	"sostituisci_g00_g01"                   :  "1",
	"numero_spazi_tra_coordinate"           :  "2",

	# config maschere
	"maschera_15mm_numeri_sostituzione_z-5" : '-15',
	"maschera_15mm_base_sostituzione_z-5"   : '-5',
}

default_templates = dict()
default_templates['config/maschere/utensile.template'] = '''
UTENSILE      
'''[1:]       
default_templates['config/maschere/intestazione.template'] = '''
INTEST        
'''[1:]       
default_templates['config/maschere/chiusura.template'] = '''
CHIUS         
'''[1:]       
default_templates['config/utensile.template'] = '''
UTENSI        
'''[1:]       
default_templates['config/intestazione.template'] = '''
INT           
'''[1:]       
default_templates['config/chiusura.template'] = '''
CHIU
'''[1:]
