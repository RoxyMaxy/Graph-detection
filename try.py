import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import matplotlib
from matplotlib.lines import Line2D

matplotlib.use('TkAgg') #Permet l'utilisation de fenêtre interactive pour déplacer des noeuds, et pour permettre aux relations de s'adapter à la position des noeuds 


# Fonction pour valider l'entrée utilisateur
def saisieValeurs(entree):
    while True:
        user_input = input(entree)
        # Vérifier si c'est un entier (positif ou négatif)
        try:
            n = int(user_input)
            if n > 0:
                return n
            else:
                print("\tErreur: Veuillez entrer un nombre entier positif (supérieur à 0)")
        except ValueError:
            print("\tErreur: Veuillez entrer un nombre entier valide")


def generer_graphe_aleatoire(n, p):
    # Génère et nettoie le graphe
    G = nx.gnp_random_graph(n, p)
    return G


def extraire_grande_composante_connexe(G, n_initial):
    # Nettoyage du graphe
    if not nx.is_connected(G):
        largest_composant_connexe = max(nx.connected_components(G), key=len)  # Garder la plus grande composante connexe
        G = G.subgraph(largest_composant_connexe).copy()
        print(f"Note: {n_initial - len(G)} noeuds supprimés (non connectés)")
        n = len(G)  # Mise à jour de n
        print(f"\tNouveau nombre de noeuds: {n}")
    return G


def detecter_cliques(G):
    # Détection des Patterns
    cliques = list(nx.find_cliques(G)) #Pour la détection des cliques

    # Filtrage : on ne garde que les noeuds appartenant à une clique d'au moins 3 noeuds
    big_clique_nodes = set().union(*(c for c in cliques if len(c) >= 3))
    
    return big_clique_nodes, cliques


def detecter_communautes(G):
    # Détection des communautés par algorithme de propagation d'étiquettes
    communautes = list(nx.community.label_propagation_communities(G))

    # Filtrage : on ne garde que les communautés d'au moins 2 noeuds
    bigCommunautes = [c for c in communautes if len(c) >= 2]

    # Dictionnaire communauté -> indice (pour la couleur)
    node_comm = {}
    for idx, comm in enumerate(bigCommunautes):
        for v in comm:
            node_comm[v] = idx
    
    return bigCommunautes, node_comm


def construire_graphe_utile(G, big_clique_nodes, node_comm):
    # On ne garde que les noeuds de clique ou de communauté
    noeudsUtiles = set(big_clique_nodes) | set(node_comm.keys())

    # Vérifier s'il y a des noeuds utiles pour la détection
    if len(noeudsUtiles) == 0:
        print("\nAucune clique ou communauté trouvée!")
        print("\tEssayez d'augmenter le nombre de noeuds ou relancez le programme.")
        return None, None, None, None

    # Coloration des noeuds
    cmap = plt.cm.tab10
    comm_colors = [cmap(i % 10) for i in range(len(node_comm))]

    # Coloration seulement pour les noeuds affichés
    colors = []
    for v in noeudsUtiles:
        if v in big_clique_nodes:
            colors.append('red')
        else:
            colors.append(comm_colors[node_comm[v]])

    # Créer un sous-graphe GPrime ne contenant que les noeuds intéressants et leurs arêtes
    GPrime = G.subgraph(noeudsUtiles).copy()
    
    return GPrime, noeudsUtiles, colors, comm_colors


def afficher_graphe(GPrime, colors, bigCommunautes, comm_colors):
    # Visualisation
    fig, ax = plt.subplots(figsize=(10, 8)) #fig, c'est la fenêtre où le graphe final s'affichera. ax s'occupe de l'affichage de chaque éléments du graphe. C'est un repère, un peu comme un filigrane

    pos = nx.spring_layout(GPrime, seed=42) #Il s'agit du calcul de la disposition des noeuds et associe à chaque noeuds ses coordonnees.

    # Traçage des arêtes restantes utiles
    edges = []
    for u, v in GPrime.edges():
        (line,) = ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]],'lightgray', alpha=0.6) #la présence de la virgule dans (line,) indique au programme de lui retourner les liaisons entre noeuds, mais pas la liste des liaisons, car ax.plot retourne une liste, normalement
        edges.append((line, u, v))

    # Affichage des noeuds selons leurs positions déterminées ci-avant par pos
    points = ax.scatter([pos[v][0] for v in GPrime.nodes()], [pos[v][1] for v in GPrime.nodes()],c=colors, s=300, zorder=5, picker=True, pickradius=5)

    # Légende simple
    legend_elements = [Line2D([0], [0], marker='o', color='w', label='Clique (≥3)', markerfacecolor='red', markersize=10)]
    for i, comm in enumerate(bigCommunautes):
        legend_elements.append(Line2D([0], [0], marker='o', color='w', label=f'Com. {i+1} ({len(comm)} noeuds)', markerfacecolor=comm_colors[i], markersize=10))
    ax.legend(handles=legend_elements, loc='upper right', fontsize=7)

    # Les Line2D marquent "où les légendes sont écrites". Ce ne sont que des objets factices, mais utiles pour un bel affichage

    ax.axis('off')  #Cette ligne supprime tous les axes, pour un affichage net
    plt.title("Cliques: coloriés en rouge.\nCommunautés: autres couleurs")
    
    return fig, ax, pos, points, edges, list(GPrime.nodes())


dragged = None  #Cette variable stocke le noeud en déplacement


def on_pick(event):
    global dragged
    if event.artist == points:  #event.artist vérifie ici que l'utilisateur a appuyé sur un noeud et non une arête
        dragged = nodes_list[event.ind[0]] #Elle stocke quel noeud l'utilisateur a cliqué.


def on_motion(event):
    global dragged
    if dragged is None or event.inaxes != ax: return
    pos[dragged] = (event.xdata, event.ydata)
    for line, u, v in edges:
        if u == dragged or v == dragged:
            line.set_data([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]])
    points.set_offsets([[pos[v][0], pos[v][1]] for v in nodes_list])
    for text, v in zip(ax.texts, nodes_list):
        text.set_position((pos[v][0], pos[v][1]))
    fig.canvas.draw_idle()


def on_release(event): #Quand l'utilisateur lâche le noeud
    global dragged
    dragged = None


def activer_interaction_souris(fig_param, ax_param, pos_param, points_param, edges_param, nodes_list_param):
    global fig, ax, pos, points, edges, nodes_list
    fig = fig_param
    ax = ax_param
    pos = pos_param
    points = points_param
    edges = edges_param
    nodes_list = nodes_list_param
    
    fig.canvas.mpl_connect('pick_event', on_pick)
    fig.canvas.mpl_connect('motion_notify_event', on_motion)
    fig.canvas.mpl_connect('button_release_event', on_release)
    #Ces fonctions ci-dessus relient respectivement chaque évènement "Clic sur un noeud", "Mouvement de la souris" et "Relâchement du clic" aux fonctions définies, un peu comme les slots en langage C++


def compteRendu(cliques, bigCommunautes):
    # Résultat ou compte rendu
    print("\n\t\tRésultats de l'analyse de graphe:")
    print("Noeuds de cliques :")
    for c in cliques:
        if len(c) >= 3:
            print(" ", sorted(c))
    print("\nCommunautés :")
    for i, comm in enumerate(bigCommunautes):
        print(f"  Communauté {i+1}: {sorted(comm)}")


def main():
    global points, nodes_list, pos, edges, fig, ax
    
    # Vérifie que n >= 3
    while True:
        n = saisieValeurs("Combien de noeuds? : n = ")
        if n >= 3:
            break
        else:
            print("\tErreur: il faut au moins 3 noeuds pour un graphe utile")
    
    p = np.log(n) / n     # C'est la probabilité qu'il existe un lien entre deux noeuds.
    
    G = generer_graphe_aleatoire(n, p)
    
    G = extraire_grande_composante_connexe(G, n)
    
    big_clique_nodes, cliques = detecter_cliques(G)
    
    bigCommunautes, node_comm = detecter_communautes(G)
    
    GPrime, noeudsUtiles, colors, comm_colors = construire_graphe_utile(G, big_clique_nodes, node_comm)
    
    if GPrime is None:
        return
    
    fig, ax, pos, points, edges, nodes_list = afficher_graphe(GPrime, colors, bigCommunautes, comm_colors)
    
    activer_interaction_souris(fig, ax, pos, points, edges, nodes_list)
    
    plt.show()
    
    compteRendu(cliques, bigCommunautes)


# Implémentation
    main()