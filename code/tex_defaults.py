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

	'PROGRAMMA'                      : 'PROGRAMMA',
	'CLIENTE'                        : 'cliente',
	'DESCRIZIONE'                    : 'Descrizione',
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
	"descrizione_max_lunghezza"             : "34",
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

# @todo: compile template defaults
default_templates = dict()
default_templates['config/maschere/utensile.template'] = '''
$COORDINATE$

'''[1:]       

default_templates['config/maschere/intestazione.template'] = '''
ERRORE
'''[1:]       

default_templates['config/maschere/chiusura.template'] = '''
ERRORE
'''[1:]       

default_templates['config/utensile.template'] = '''
;
M2$NUMEROMOTORE$ S$VELOCITAROTAZIONEFRESA$$1:inizio_programma.template$
;
; ================================== M$NUMEROMOTORE$ $UTENSILE$ =====================================
G90 G0 X$PRIMAX$ Y$PRIMAY$ A$PRIMAA$ B$PRIMAB$
;
L365=0
L385=$LUNGHEZZAUTENSILE$
L386=$NUMEROMOTORE$
;
(TCP,1)
;
G90 G0 X$PRIMAX$ Y$PRIMAY$
;
$COORDINATE$

'''[1:]       

default_templates['config/intestazione.template'] = '''
;                             * * * $PROGRAMMA$ * * *
; ==============================================================================
;                                                      "$CLIENTE$"
; $DESCRIZIONE$
$RIGHECODICI$
;
; ==============================================================================
;                             $UTENSILI$
;  <R$ROBOT$>  $POSIZIONEDIMA$
;                                             $DATA$ $PROGRAMMATORE$
;
; ==============================================================================

'''[1:]       


default_templates['config/chiusura.template'] = '''
;
(TCP)
;
(UAO,0)
;
G90 G0 Z$Z_zero$
G90 G0 Y$Y_margine$
;
A$A_zero$ B$B_zero$
;
X$X_zero$ Y$Y_zero$ Z$Z_zero$
;
M5
;

'''[1:]


default_templates['config/riga_codice.template'] = '''
;                                                      [$CODICE$] $REV$

'''[1:]
