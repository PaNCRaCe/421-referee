# -*- coding: utf-8 -*-
"""
Created on Tue Mar  7 14:29:59 2017

@author: geoffrey
"""
#import irclib
import ircbot

from libPartie import JoueurInvalide, SelectionInvalide, CommandeInvalide

from libPartie import Partie

from shlex import split as shlex_split

# done : bug auto kickage + kick mauvais joueur
# TODO : mode insultes et random taunts
# TODO : IA
# done : commande lance all, lance 64

# TODO : BUG : Excess flood
#This quit message shows that you attempted to send too much data to the IRC server, in too short a time period,
#and the server thought you were attempting to flood it. A good way to prevent this is to enable flood protection
#in your IRC client. mIRC users may click File -> Options -> IRC -> Flood, and then check Enable flood protection.
#The default values should be sufficient for most users.

# TODO : messages sur plusieurs lignes en 1 seule commande (equivalent \n ?)

# done : empêcher la commande demarrer si partie en cours
# done : dés à X faces (de 2 à 9)

class b421(ircbot.SingleServerIRCBot):
    def __init__(self, channel, name):
        self.CHANNEL = channel
        ircbot.SingleServerIRCBot.__init__(self, [("127.0.0.1", 6667)],
                                           name, name)
        self.last_serv = None

        self.partie = Partie(self)

    def __del__(self):
        self.die()

#        self.messages =["bot421"]

    def on_welcome (self, serv, ev):
        #action lors de la connexion à IRC
        serv.join(self.CHANNEL)

    def on_kick(self, serv, ev):
        canal = ev.target()
        name_src = ev.source().split("!")[0] # pseudo de l'emetteur
        name_dst = ev.arguments()[0] # pseudo de la cible

        if self._realname == name_src: # nous sommes l'emetteur du kick
            pass
        elif self._realname == name_dst: # bous sommes la cible
            serv.privmsg(canal, "%s, fils de pute !" % name_src)
            serv.join(canal)
            serv.kick(self.CHANNEL, name_src, "Casse toi pov'CON!") # si droits op permantents?
        else:
            serv.kick(self.CHANNEL, name_src, "C'est moi qui kick ici!")

    def on_pubmsg(self, serv, ev):

        self.last_serv = serv

        canal = ev.target()
        name = ev.source().split("!")[0]
        raw_text = ev.arguments()[0].lower()

        if name == self._realname or name == self._nickname: # nous sommes l'emetteur du msg
            return

        try:
            args = shlex_split(raw_text)
        except ValueError:
            return

        cmd = args[0]
        args = args[1:]

        if self._nickname in raw_text:
            serv.privmsg(canal, "Ferme ta gueule %s !" % name)

        elif cmd == "participer":
            self.partie.nouveau_joueur(name)

        elif cmd == "demarrer":

            try:
#                assert len(args) == 1 # AssertionError
                N_jetons = int(args[0]) # ValueError
            except IndexError:
                N_jetons = None
            except ValueError:
                serv.privmsg(canal, "Apran A tappé!")
                return

            try:
                N_faces = int(args[1]) # IndexError
            except IndexError:
                N_faces = None
            except ValueError:
                serv.privmsg(canal, "Apran A tappé!")
                return

            try:
                self.partie.start(nbr_jetons=N_jetons, nbr_faces=N_faces)
            except CommandeInvalide, e:
                serv.privmsg(canal, e)
                return

        elif cmd == "lance":


            try:
                if len(args) == 0:
                    liste_rejoues = None # premier coup
                elif args[0] == "tout":
                    liste_rejoues = "tout"
                elif len(args) == 1:
                    liste_rejoues = [int(a) for a in args[0]]  # cmd type lance 43
                else:
                    liste_rejoues = [int(a) for a in args]  # cmd type lance 4 3
            except ValueError:
                serv.privmsg(canal, "Apprent a tapez!")
                return

            try:
                self.partie.lancer(name, liste_rejoues)
            except (JoueurInvalide, SelectionInvalide, CommandeInvalide), e:
                serv.privmsg(canal, e)
                return

        elif cmd == "garde":
            try:
                self.partie.garde(name)
            except (JoueurInvalide, CommandeInvalide), e:
                serv.privmsg(canal, e)
                return

        elif cmd == "scores":
#            try:
            self.partie.print_score()
#            except JoueurInvalide, e:
#                serv.privmsg(canal, e)

        elif cmd == "historique":
#            try:
            self.partie.print_historique()
#            except JoueurInvalide, e:
#                serv.privmsg(canal, e)

        elif cmd == "quitter":
            try:
                self.partie.enlever_joueur(name)
            except CommandeInvalide, e:
                serv.privmsg(canal, e)
                return

        elif cmd == "help":
            serv.privmsg(canal, "tu m'as pris pour qui?")

        elif cmd == "aide":
            serv.privmsg(canal, "-participer : s'inscrire au jeu")
            serv.privmsg(canal, "-quitter    : se désinscrire du jeu")
            serv.privmsg(canal, "-demarrer   : lancer la partie")
            serv.privmsg(canal, "-lance      : lancer les des")
            serv.privmsg(canal, "-lance tout : relancer les 3 des")
            serv.privmsg(canal, "-lance x y  : relancer les des x et y")
            serv.privmsg(canal, "-garde      : garder sa combinaison")
            serv.privmsg(canal, "-scores     : afficher les scores")
            serv.privmsg(canal, "-historique : afficher l'evolution des scores")


    def send_msg(self, msg):
        self.last_serv.privmsg(self.CHANNEL, msg)

    def kick(self, name, msg):
        if not self._nickname == name:
            self.last_serv.kick(self.CHANNEL, name, msg)


if __name__ == "__main__":
    CHANNEL = "#421"
    NAME = "arbitre"
    b421(CHANNEL, NAME).start()
