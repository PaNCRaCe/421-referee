# -*- coding: utf-8 -*-
"""
Created on Wed Mar  8 17:04:41 2017

@author: breteau
"""

class JoueurInvalide(Exception):
    pass

class SelectionInvalide(Exception):
    pass

class CommandeInvalide(Exception):
    pass

from lib421 import combinaison, points, label_combinaison, get_des
import numpy as np
from itertools import cycle

# TODO : enlever et kicker adversaire inactif en cours de partie
# done : tester tirage aléatoire -> OUI
# done : historique des scores
# done : nombre de jetons auto
# done : lance tout
# done : main chaude
# TODO : tester main chaude avec N joueurs


class Partie():

    def __init__(self, com, pseudos=[], debug=False):
        self.pseudos = pseudos
        self.flag_started = False

        self.FLAG_DEBUG = False # pour debugger selon certains etats

        for pseudo in pseudos:
            self.nouveau_joueur(pseudo)

        self.com = com

        self.historique = []

        self.currentStates = None

    def send_msg(self, msg):
        self.com.send_msg(msg)

    def nouveau_joueur(self, pseudo):
        if self.flag_started is True:
            raise CommandeInvalide("La partie a déjà commencée... sans toi!")

        if not pseudo in self.pseudos:
            self.pseudos.append(pseudo)
            self.send_msg("%s a été ajouté à la liste des participants" % pseudo)

    def enlever_joueur(self, pseudo):
        if self.flag_started is True:
            raise CommandeInvalide("On ne part pas sans avoir fini son assiette!")

        if pseudo in self.pseudos:
            self.pseudos.remove(pseudo)

    def start(self, nbr_jetons=None, nbr_faces=None):

        if self.flag_started is True:
            raise CommandeInvalide("Une partie est déjà en cours!")

        if nbr_jetons is None:
            nbr_jetons = len(self.pseudos) * 10 + 1

        if len(self.pseudos) == 0:
            raise CommandeInvalide("Personne n'est inscrit...")
        elif len(self.pseudos) == 1:
            raise CommandeInvalide("T'es tout seul à jouer! Va plutôt mater un film de cul.")
        elif nbr_jetons < 1:
            raise CommandeInvalide("Le nombre de jetons %d est invalide!" % nbr_jetons)
        elif nbr_faces is not None and (nbr_faces < 2 or nbr_faces > 9):
            raise CommandeInvalide("Seuls les dés de 2 à 9 faces sont autorisés")

        np.random.shuffle(self.pseudos)

        self.currentStates = {}
        for pseudo in self.pseudos:
            self.currentStates[pseudo] = {"combi": None, "pts_combi": None, "score": 0, "num_coup": 0}

        self.iter_joueurs = cycle(self.pseudos)

        self.first_to_play = self.iter_joueurs.next()
        self.next_to_play = self.first_to_play

        self.decharge = False
        self.N_JETONS = nbr_jetons
        self.N_lancer_max = None

        self.flag_started = True
        self.flag_egalite_winner = False
        self.flag_egalite_looser = False

        self.send_msg("C'EST PARTI MON KIKI!")

        if nbr_faces is None:
            self.nbr_faces = 6
        else:
            self.nbr_faces = nbr_faces
            self.send_msg("dés à %d faces" % self.nbr_faces)

        self.send_msg("%d jetons en jeu" % nbr_jetons)
        self.print_next_player()

        self.historique = []

    def lancer(self, pseudo, rejoues=None):

        if self.flag_started is False:
            raise CommandeInvalide("La partie n'a pas commencée!")

        if not self.next_to_play == pseudo:
            raise JoueurInvalide("%s, ce n'est pas à toi de jouer!" % pseudo)

        if self.flag_egalite_winner is True or self.flag_egalite_looser is True:
            if rejoues is not None and rejoues is not "tout" and len(rejoues) != 0:
                raise CommandeInvalide("Lance 3 dés pour ton premier coup...")

            self._main_chaude(pseudo)
            return

        if self.currentStates[pseudo]["combi"] is None: # premier coup
            if rejoues is not None and rejoues is not "tout" and len(rejoues) != 0:
                raise CommandeInvalide("Lance 3 dés pour ton premier coup...")

            tirage = np.random.randint(1, self.nbr_faces+1, 3)
#            print tirage
            code = combinaison(tirage, self.nbr_faces)
            pts = points(code)

            self.send_msg("%s lance 3 dés et obtiens %s : %s" % (pseudo, tirage, label_combinaison(code)))
            if code > 4400 and all([code > st["combi"] for st in self.currentStates.itervalues()]):
                self.send_msg("chateux!")
        else:
            if rejoues is None or len(rejoues) <= 0:
                raise SelectionInvalide("Sélectione des dés à rejouer!")

            if rejoues is "tout":
                rejoues = get_des(self.currentStates[pseudo]["combi"])
                tirage = np.random.randint(1, self.nbr_faces+1, 3)
                values = tirage
            else:

                values = get_des(self.currentStates[pseudo]["combi"])
                for rejoue in rejoues:
                    toDelete = np.where(np.array(values) == rejoue)[0]
                    if toDelete.size == 0:
                        raise SelectionInvalide("Pas de dé %s à rejouer!" % rejoue)

                    values = np.delete(values, toDelete[0])

                N_relances = len(rejoues)

                tirage = np.random.randint(1, self.nbr_faces+1, N_relances)
                values = np.append(values, tirage)

            code = combinaison(values, self.nbr_faces)
            pts = points(code)

            self.send_msg("%s relance %s et obtiens %s : %s" % (pseudo, rejoues, tirage, label_combinaison(code)))
            if (np.sort(tirage) == np.sort(rejoues)).all():
                self.send_msg("ahah!")

        self.currentStates[pseudo]["combi"] = code
        self.currentStates[pseudo]["pts_combi"] = pts

        self.currentStates[pseudo]["num_coup"] += 1

        if self.N_lancer_max is not None:
            N_lancer_max = self.N_lancer_max
        else:
            N_lancer_max = 3

        if self.currentStates[pseudo]["num_coup"] == N_lancer_max:

            self.next_to_play = self.iter_joueurs.next()
#            print "ici2", pseudo, self.next_to_play

            if self.N_lancer_max is None:
                self.N_lancer_max = 3

            if self.next_to_play  == self.first_to_play: # fin du tour
                self._fin_tour()
            else:
                self.print_next_player()


    def garde(self, pseudo):

        if self.flag_started is False:
            raise CommandeInvalide("La partie n'a pas commencée!")

        if not self.next_to_play == pseudo:
            raise JoueurInvalide("Ce n'est pas à %s de jouer!" % pseudo)

        if self.currentStates[pseudo]["combi"] is None:
            raise CommandeInvalide("Tu dois jouer au moins une fois!")

        if self.N_lancer_max is None:
            self.N_lancer_max = self.currentStates[pseudo]["num_coup"]

        self.next_to_play = self.iter_joueurs.next()

        if self.next_to_play  == self.first_to_play: # fin du tour
            self._fin_tour()
        else:
            self.print_next_player()


    def _fin_tour(self):

        assert all([cs["combi"] is not None for cs in self.currentStates.itervalues()])

        best = 0
        worst = 9999
        self.flag_egalite_winner = False
        self.flag_egalite_looser = False

        for pseudo, etat in self.currentStates.iteritems():
            if etat["combi"] > best:
                best = etat["combi"]
                winner = pseudo
                self.flag_egalite_winner = False
            elif etat["combi"] == best:
                winner = np.append(winner, pseudo)
                self.flag_egalite_winner = True

            if etat["combi"] < worst:
                worst = etat["combi"]
                looser = pseudo
                self.flag_egalite_looser = False
            elif etat["combi"] == worst:
                looser = np.append(looser, pseudo)
                self.flag_egalite_looser = True

        if self.flag_egalite_winner is True or self.flag_egalite_looser is True:

            self.egaliteStates_w = {}
            self.egaliteStates_l = {}

            if self.flag_egalite_winner is True:
                for jj in winner:
                    self.egaliteStates_w[jj] = {"combi": None}

            if self.flag_egalite_looser is True:
                for jj in looser:
                    self.egaliteStates_l[jj] = {"combi": None}

            self.print_score()
            self.send_msg("main chaude !")

            try:
                self.next_to_play = self.egaliteStates_w.keys()[0]
            except IndexError:
                self.next_to_play = self.egaliteStates_l.keys()[0]

            self.print_next_player()

            return

#        while self.flag_egalite_winner is True:
#            departage = 0
#            for pseudo in winner:
#                values = np.random.randint(1, self.nbr_faces+1, 3)
#                force = combinaison(values, self.nbr_faces)
#                if force > departage:
#                    self.flag_egalite_winner = False
#                    win = pseudo
#                elif force == departage:
#                    self.flag_egalite_winner = True
#                    win = np.append(win, pseudo)
#            winner = win
#        while self.flag_egalite_looser is True:
#            departage = 9999
#            for pseudo in looser:
#                if pseudo == win:
#                    continue
#
#                values = np.random.randint(1, self.nbr_faces+1, 3)
#                force = combinaison(values, self.nbr_faces)
#                if force < departage:
#                    self.flag_egalite_looser = False
#                    los = pseudo
#                elif force == departage:
#                    self.flag_egalite_looser = True
#                los = np.append(win, pseudo)
#            looser = los

        flag_debut_decharge = False

        N_echanges = self.currentStates[winner]["pts_combi"] # non modifié en cas d'égalité
#        N_echanges = points(best)

        if self.decharge is True:
#            N_echanges = points(best)
            if self.currentStates[winner]["score"] < N_echanges:
                N_echanges = self.currentStates[winner]["score"]

            self.currentStates[winner]["score"] -= N_echanges

        else:
            if self.N_JETONS - np.sum([state["score"] for state in self.currentStates.itervalues()]) <=  N_echanges:
                N_echanges = self.N_JETONS - np.sum([state["score"] for state in self.currentStates.itervalues()])
                self.decharge = True
                flag_debut_decharge = True

        self.currentStates[looser]["score"] += N_echanges

        self.print_score()
        self.historique.append([self.currentStates[ps]["score"] for ps in self.pseudos])

#        if self.FLAG_DEBUG is True:
#            import pdb; pdb.set_trace()
#            self.FLAG_DEBUG = False # DEBUG

        for pseudo in self.pseudos:
            self.currentStates[pseudo]["combi"] = None
            self.currentStates[pseudo]["pts_combi"] = None
            self.currentStates[pseudo]["num_coup"] = 0

        self.N_lancer_max = None

        if self.decharge is True and np.any([state["score"] == 0 for state in self.currentStates.itervalues()]):
            self._fin_partie()
        else:
            if flag_debut_decharge is True:
                self.send_msg("décharge !")


            while not self.next_to_play == looser:
                self.next_to_play = self.iter_joueurs.next()
            self.first_to_play = looser

#            print "ici", self.first_to_play, self.next_to_play

            self.print_next_player()


    def _main_chaude(self, pseudo):

        if not self.next_to_play == pseudo:
            raise JoueurInvalide("%s, ce n'est pas à toi de jouer!" % pseudo)

        assert self.flag_egalite_winner is True or self.flag_egalite_looser is True


#        import pdb; pdb.set_trace()
#        print "main chaude"
#        print self.flag_egalite_winner, self.flag_egalite_looser
#        print self.egaliteStates_w
#        print self.egaliteStates_l

        tirage = np.random.randint(1, self.nbr_faces+1, 3)
        code = combinaison(tirage, self.nbr_faces)

#        sorted_values = np.sort(tirage) # par ordre croissant
#        dec_value = np.sum([v * 10**i for i, v in enumerate(sorted_values)]) # valeur decimale

        self.send_msg("%s lance 3 dés et obtiens %s : %s" % (pseudo, tirage, label_combinaison(code)))

        if pseudo in self.egaliteStates_w.keys():
            self.egaliteStates_w[pseudo]["combi"] = code

        if pseudo in self.egaliteStates_l.keys():
            self.egaliteStates_l[pseudo]["combi"] = code

        if self.flag_egalite_winner is True:

            if not np.all([state["combi"] is not None for state in self.egaliteStates_w.values()]):
                for name, state in self.egaliteStates_w.iteritems():
                    if state["combi"] is None:
                        while not self.next_to_play == name:
                            self.next_to_play = self.iter_joueurs.next()
                        # self.next_to_play = name
                        self.print_next_player()
                        return

            if set(self.egaliteStates_w.keys()) == set(self.pseudos): # tous joueurs à égalité
                flag_allPlayers = True # test ok à 4j
                self.egaliteStates_l = {}
#                self.FLAG_DEBUG = True # DEBUG
            else:
                flag_allPlayers = False

                if self.flag_egalite_winner is True and self.flag_egalite_looser is True: # 2 egalites distinctes : gagnant ou perdant mais pas tous -> OK!!!
                    print "win", self.egaliteStates_w.keys() # DEBUG
                    print "los", self.egaliteStates_l.keys() # DEBUG
#                    self.FLAG_DEBUG = True # DEBUG

            comb_max = 0
            comb_min = 9999
            for name, state in self.egaliteStates_w.iteritems():
                if state["combi"] > comb_max:
                    self.flag_egalite_winner = False
                    win = name
                    comb_max = state["combi"]
                elif state["combi"] == comb_max:
                    self.flag_egalite_winner = True
                    win = np.append(win, name)

                if flag_allPlayers is True and state["combi"] < comb_min:
                    self.flag_egalite_looser = False
                    los = name
                    comb_min = state["combi"]
                elif flag_allPlayers is True and state["combi"] == comb_min:
                    self.flag_egalite_looser = True
                    los = np.append(los, name)


            if flag_allPlayers is True: #
                if self.flag_egalite_looser is True: # nouvelle main chaude
                    self.egaliteStates_l = {}
                    for jj in los:
                        self.egaliteStates_l[jj] = {"combi": None}
                else:
                    dec_value = np.sum([v * 10**i for i, v in enumerate(np.sort(get_des(self.currentStates[los]["combi"])))])
                    self.currentStates[los]["combi"] = dec_value # on modifie le code sans changer le nombre de pts

            if self.flag_egalite_winner is True: # nouvelle main chaude
                self.egaliteStates_w = {}
                for jj in win:
                    self.egaliteStates_w[jj] = {"combi": None}

                while not self.next_to_play == win[0]:
                    self.next_to_play = self.iter_joueurs.next()
#                self.next_to_play = win[0]
                self.print_next_player()
                return
            else:
                dec_value = np.sum([v * 10**i for i, v in enumerate(np.sort(get_des(self.currentStates[win]["combi"])))])
                self.currentStates[win]["combi"] = 9000 + dec_value # on modifie le code sans changer le nombre de pts

            if flag_allPlayers is True and self.flag_egalite_looser is True: # nouvelle main chaude perdante uniquement

                while not self.next_to_play == los[0]:
                    self.next_to_play = self.iter_joueurs.next()
#                self.next_to_play = los[0]
                self.print_next_player()
                return

        if self.flag_egalite_looser is True and not np.all([state["combi"] is not None for state in self.egaliteStates_l.values()]): # tous les perdants n'ont pas joués

            for pseudo, state in self.egaliteStates_l.iteritems():
                if state["combi"] is None:
                    while not self.next_to_play == pseudo:
                        self.next_to_play = self.iter_joueurs.next()
#                    self.next_to_play = pseudo
                    self.print_next_player()
                    return

        elif self.flag_egalite_looser is True:
            comb_min = 9999
            for name, state in self.egaliteStates_l.iteritems():
                if state["combi"] < comb_min:
                    self.flag_egalite_looser = False
                    los = name
                    comb_min = state["combi"]
                elif state["combi"] == comb_min:
                    self.flag_egalite_looser = True
                    los = np.append(los, name)

            if self.flag_egalite_looser is True: # nouvelle main chaude
                self.egaliteStates_l = {}
                for jj in los:
                    self.egaliteStates_l[jj] = {"combi": None}

            else:
                dec_value = np.sum([v * 10**i for i, v in enumerate(np.sort(get_des(self.currentStates[los]["combi"])))])
                self.currentStates[los]["combi"] = dec_value # on modifie le code sans changer le nombre de pts

        if np.all([state["combi"] is not None for state in self.egaliteStates_w.values()]) and \
                np.all([state["combi"] is not None for state in self.egaliteStates_l.values()]):
            # tous ont joué

#            print self.next_to_play, self.first_to_play

            self._fin_tour() # fin de tour avec les codes modifiés

#            print self.next_to_play, self.first_to_play
#            print "fin main chaude"
#            import pdb; pdb.set_trace()


    def _fin_partie(self):


        assert self.decharge is True and any([cs["score"] == 0 for cs in self.currentStates.itervalues()])

        for pseudo, state in self.currentStates.iteritems():
            if state["score"] == 0:
                self.send_msg("%s EST VAINQUEUR !" % pseudo)

        for pseudo, state in self.currentStates.iteritems():
            if not state["score"] == 0:
                self.com.kick(pseudo, "dégage, LOOSER!")

        self.flag_started = False


    def print_tirage(self, pseudo=None):

        if self.currentStates is None: # aucune partie n'a été lancée
            return

        if pseudo is None:
            for ps, state in self.currentStates.iteritems():
                self.send_msg("%s : %s" % (ps, label_combinaison(state["combi"])))
        else:
            self.send_msg("%s : %s" % (pseudo, label_combinaison(self.currentStates[pseudo]["combi"])))


    def print_score(self, pseudo=None):

        if self.currentStates is None: # aucune partie n'a été lancée
            return

        if pseudo is None:
            self.send_msg("_______________________")
            for ps, state in self.currentStates.iteritems():
                self.send_msg("%s (%2d): %s" % (ps, state["score"], label_combinaison(state["combi"])))
            self.send_msg("_______________________\n")
        else:
            self.send_msg("%s (%2d): %s" % (pseudo, self.currentStates[pseudo]["score"], label_combinaison(self.currentStates[pseudo]["combi"])))

    def print_next_player(self):

        if self.currentStates is None: # aucune partie n'a été lancée
            return

        if self.N_lancer_max is None:
            self.send_msg("à %s de commencer..." % self.next_to_play)
        else:
            self.send_msg("à %s de jouer (%d coups)..." % (self.next_to_play, self.N_lancer_max))

    def print_historique(self):

        if self.currentStates is None: # aucune partie n'a été lancée
            return

        self.send_msg("    " + "".join(["%15s" % ss for ss in self.pseudos]))
        for i, row in enumerate(self.historique):
            self.send_msg("%3d " % (i+1) + "".join(["%15d" % sc for sc in row]))



if __name__ == "__main__":

    class DEBUGGER():

        def send_msg(self, msg):
            print msg

        def kick(self, pseudo, msg):
            print msg
            print "KICK %s" % pseudo

    from lib421 import InvalidCode

    com = DEBUGGER()

    pps = ["doudou", "tchupi", "hubert", "playerX"]
    pa = Partie(com, pps)
    pa.start()
    while True:
        try:
            nextPlayer = pa.next_to_play
            pa.lancer(nextPlayer)
            des = get_des(pa.currentStates[nextPlayer]["combi"])[1:]
            nextPlayer = pa.next_to_play
            pa.lancer(nextPlayer, des)

            de = [get_des(pa.currentStates[nextPlayer]["combi"])[-1]]
            nextPlayer = pa.next_to_play
            pa.lancer(nextPlayer, de)
        except InvalidCode, e: # redemarrer la boucle en cas de main chaude
            if pa.currentStates[nextPlayer]["combi"] is None:
                continue
            else:
                raise e
        except SelectionInvalide, e: # pas de dé selectionné
            nextPlayer = pa.next_to_play
            pa.lancer(nextPlayer, "tout")
            continue

        except CommandeInvalide, e:
            if pa.flag_started is False:
                pa.start()

            continue
