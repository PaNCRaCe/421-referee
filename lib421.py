# -*- coding: utf-8 -*-
"""
Created on Fri Mar 10 10:18:05 2017

@author: breteau
"""

import numpy as np

class InvalidCode(Exception):
    pass

class InvalidCombinaison(Exception):
    pass

def label_combinaison(code):

    if code is None: # pas joué
        return "---"

    try:
        c, d1, d2, d3 = [int(c) for c in "%04d" % code]
    except:
        raise InvalidCode("Le code %d est invalide" % code)

    if c == 6:
        return "421 !"
    elif c == 5:
        return "As purs"
    elif c == 4:
        if d3 == 1:
            return "%d purs" % d1
        else:
            return "brelan de %d" % d1
    elif c == 3:
        return "suite %s" % str(code)[1:]
    elif c == 2:
        return "nénette"
    elif c == 1:
        return str(code)[1:]
    elif c == 9:
        return "main chaude GAGNANTE"
    elif c == 0:
        return "main chaude PERDANTE"
    else:
        raise InvalidCode("Le code %d est invalide" % code)


def points(code):

    try:
        c, d1, _, _ = [int(c) for c in str(code)]
    except:
        raise InvalidCode("Le code %d est invalide" % code)

    if c == 6:
        return 10
    elif c == 5:
        return 7
    elif c == 4:
        return d1
    elif c == 3:
        return 2
    elif c == 2:
        return 4
    elif c == 1:
        return 1
    else:
        raise InvalidCode("Le code %d est invalide" % code)

def get_des(code):
    
    if code is None:
        raise InvalidCode("Le joueur n'a pas encore joué son premier coup")
    
    try:
        assert code >= 111
        des = np.array([int(c) for c in "%04d" % code][1:])
        assert des.size == 3
    except:
        raise InvalidCode("Le code %d est invalide" % code)

    return des

def combinaison(valeurs, nbr_faces=6):

    if not len(valeurs) == 3 or any([vv not in range(1,nbr_faces+1) for vv in valeurs]):
        raise InvalidCombinaison("Le tirage %s n'est pas valide" % valeurs)

    sorted_values = np.sort(valeurs) # par ordre croissant
    dec_value = np.sum([v * 10**i for i, v in enumerate(sorted_values)]) # valeur decimale
    sorted_values = sorted_values[::-1] # par ordre décroissant
    if dec_value == 421:
        code = 6
#        pts = 10
    elif dec_value == 111:
        code = 5
#        pts = 7
    elif np.all([v == sorted_values[0] for v in sorted_values]) \
            or sorted_values[1] == sorted_values[2] == 1:
        code = 4
#        pts = sorted_values[0]
    elif np.all([sorted_values[0] == v + i for i, v in enumerate(sorted_values)]): # suite
        code = 3
#        pts = 2
    elif dec_value == 221:
        code = 2
#        pts = 4
    else:
        code = 1
#        pts = 1

    return 1000 * code + dec_value
