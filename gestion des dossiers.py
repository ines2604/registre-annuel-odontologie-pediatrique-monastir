import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import re
import os
from datetime import datetime


import sys

if getattr(sys, 'frozen', False):
    # Application exécutée depuis le .exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Application exécutée depuis Python
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, 'registre.db')

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS registre (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        annee TEXT NOT NULL,
        nom TEXT,
        prenom TEXT,
        numero_fiche TEXT,
        numero_dossier TEXT
    )
''')
conn.commit()


def migrer_base_donnees():
    """Ajoute les colonnes nom/prenom si elles n'existent pas encore et
    migre les données de l'ancienne colonne nom_prenom (si présente)."""
    cursor.execute("PRAGMA table_info(registre)")
    colonnes = [col[1] for col in cursor.fetchall()]

    if 'nom' not in colonnes:
        cursor.execute("ALTER TABLE registre ADD COLUMN nom TEXT")
    if 'prenom' not in colonnes:
        cursor.execute("ALTER TABLE registre ADD COLUMN prenom TEXT")
    conn.commit()

    cursor.execute("PRAGMA table_info(registre)")
    colonnes = [col[1] for col in cursor.fetchall()]

    if 'nom_prenom' in colonnes:
        cursor.execute('''
            SELECT id, nom_prenom FROM registre
            WHERE nom_prenom IS NOT NULL AND nom_prenom != ''
              AND (nom IS NULL OR nom = '')
        ''')
        lignes = cursor.fetchall()
        for ligne_id, nom_prenom in lignes:
            parties = nom_prenom.strip().split(' ', 1)
            nom = parties[0]
            prenom = parties[1] if len(parties) > 1 else ''
            cursor.execute("UPDATE registre SET nom = ?, prenom = ? WHERE id = ?",
                            (nom, prenom, ligne_id))
        conn.commit()


migrer_base_donnees()


try:
    cursor.execute('DROP INDEX IF EXISTS idx_numero_fiche_unique')
    cursor.execute('DROP INDEX IF EXISTS idx_numero_dossier_unique')
    cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_numero_fiche_par_annee ON registre(annee, numero_fiche)')
    cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_numero_dossier_par_annee ON registre(annee, numero_dossier)')
    conn.commit()
except sqlite3.Error:
    pass


# Nombre de dossiers pré-créés automatiquement pour chaque nouvelle année
NOMBRE_DOSSIERS_AUTO = 2000


FONT_FAMILY = "Segoe UI"

BG_MAIN        = "#F3F4F6"   # fond général
SIDEBAR_BG     = "#1E293B"   # fond du menu latéral
SIDEBAR_ACTIVE = "#334155"   # item de menu sélectionné
SIDEBAR_TEXT   = "#CBD5E1"
SIDEBAR_TEXT_ACTIVE = "#FFFFFF"

ACCENT         = "#4F46E5"   # violet/indigo (actions principales)
ACCENT_HOVER   = "#4338CA"
ACCENT_LIGHT   = "#EEF2FF"

WARNING        = "#F59E0B"   # modifier
WARNING_HOVER  = "#D97706"

DANGER         = "#EF4444"   # supprimer
DANGER_HOVER   = "#DC2626"

CARD_BG        = "#FFFFFF"
BORDER         = "#E5E7EB"
ROW_ALT        = "#F9FAFB"
TEXT_DARK      = "#111827"
TEXT_MUTED     = "#6B7280"

NOM_SERVICE = "Service d'Odontologie Pédiatrique et Prévention"


def bouton_stylise(parent, text, command, bg=ACCENT, hover=ACCENT_HOVER, fg="white",
                    font_size=10, bold=True, padx=16, pady=8):
    btn = tk.Button(parent, text=text, command=command, bg=bg, fg=fg,
                     activebackground=hover, activeforeground=fg,
                     font=(FONT_FAMILY, font_size, "bold" if bold else "normal"),
                     relief="flat", bd=0, padx=padx, pady=pady, cursor="hand2")
    btn.bind("<Enter>", lambda e: btn.config(bg=hover))
    btn.bind("<Leave>", lambda e: btn.config(bg=bg))
    return btn


def entree_stylisee(parent, width=30, font_size=11):
    frame = tk.Frame(parent, bg=BORDER, bd=0, highlightthickness=1,
                      highlightbackground=BORDER, highlightcolor=ACCENT)
    entry = tk.Entry(frame, font=(FONT_FAMILY, font_size), relief="flat",
                      bd=8, bg="white", fg=TEXT_DARK, width=width)
    entry.pack(fill="both", expand=True)

    def on_focus_in(e):
        frame.config(highlightbackground=ACCENT, highlightthickness=2)

    def on_focus_out(e):
        frame.config(highlightbackground=BORDER, highlightthickness=1)

    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)
    return frame, entry


def champ_formulaire(parent, label_text, row, width=32):
    tk.Label(parent, text=label_text, font=(FONT_FAMILY, 10, "bold"),
              bg="white", fg=TEXT_DARK).grid(row=row, column=0, sticky="w", padx=25, pady=(14, 4))
    frame, entry = entree_stylisee(parent, width=width)
    frame.grid(row=row + 1, column=0, sticky="ew", padx=25)
    return entry



def centrer_fenetre(fenetre):
    fenetre.update_idletasks()
    largeur = fenetre.winfo_width()
    hauteur = fenetre.winfo_height()
    x = (fenetre.winfo_screenwidth() // 2) - (largeur // 2)
    y = (fenetre.winfo_screenheight() // 2) - (hauteur // 2)
    fenetre.geometry(f"+{x}+{y}")


def configurer_fenetre_secondaire(fenetre, titre, largeur=420):
    fenetre.title(titre)
    fenetre.configure(bg="white")
    fenetre.resizable(False, False)
    fenetre.transient(root)
    fenetre.grab_set()

    entete = tk.Frame(fenetre, bg=ACCENT, height=54)
    entete.pack(fill="x")
    entete.pack_propagate(False)
    tk.Label(entete, text=titre, font=(FONT_FAMILY, 13, "bold"),
             bg=ACCENT, fg="white").pack(side="left", padx=20)

    corps = tk.Frame(fenetre, bg="white")
    corps.pack(fill="both", expand=True)
    fenetre.corps = corps

    fenetre._largeur_cible = largeur
    return corps


def finaliser_fenetre(fenetre):
    largeur = getattr(fenetre, "_largeur_cible", 420)
    fenetre.update_idletasks()
    fenetre.geometry(f"{largeur}x{fenetre.winfo_reqheight()}")
    centrer_fenetre(fenetre)


def afficher_erreur(titre, message):
    erreur_win = tk.Toplevel(root)
    configurer_fenetre_secondaire(erreur_win, titre, largeur=380)
    corps = erreur_win.corps
    tk.Label(corps, text=message, font=(FONT_FAMILY, 11), bg="white", fg=TEXT_DARK,
              pady=20, padx=25, wraplength=330, justify="left").pack()
    bouton_stylise(corps, "OK", erreur_win.destroy, bg=ACCENT, hover=ACCENT_HOVER,
                   padx=30).pack(pady=(0, 20))
    finaliser_fenetre(erreur_win)


def valider_annee(annee):
    return bool(re.match(r"^\d{4}$", annee.strip()))


# ----------------------------------------------------------------------
#  État de l'application
# ----------------------------------------------------------------------
annee_courante = None
tree = None
sidebar_boutons = {}


def lister_annees_existantes():
    cursor.execute("SELECT DISTINCT annee FROM registre ORDER BY annee")
    annees = [row[0] for row in cursor.fetchall()]
    return annees


# ----------------------------------------------------------------------
#  Barre latérale (navigation par année)
# ----------------------------------------------------------------------

def construire_sidebar():
    for widget in sidebar_liste.winfo_children():
        widget.destroy()
    sidebar_boutons.clear()

    for annee in sorted(onglets_annees, reverse=True):
        est_active = (annee == annee_courante)
        item = tk.Frame(sidebar_liste, bg=SIDEBAR_ACTIVE if est_active else SIDEBAR_BG)
        item.pack(fill="x")

        indicateur = tk.Frame(item, bg=ACCENT if est_active else (SIDEBAR_ACTIVE if est_active else SIDEBAR_BG), width=4)
        indicateur.pack(side="left", fill="y")

        lbl = tk.Label(item, text=f"📅  {annee}",
                        font=(FONT_FAMILY, 11, "bold" if est_active else "normal"),
                        bg=SIDEBAR_ACTIVE if est_active else SIDEBAR_BG,
                        fg=SIDEBAR_TEXT_ACTIVE if est_active else SIDEBAR_TEXT,
                        anchor="w", padx=16, pady=12, cursor="hand2")
        lbl.pack(fill="x")

        def on_click(e, a=annee):
            selectionner_annee(a)

        def on_enter(e, it=item, lb=lbl, active=est_active):
            if not active:
                it.config(bg=SIDEBAR_ACTIVE)
                lb.config(bg=SIDEBAR_ACTIVE)

        def on_leave(e, it=item, lb=lbl, active=est_active):
            if not active:
                it.config(bg=SIDEBAR_BG)
                lb.config(bg=SIDEBAR_BG)

        for w in (item, lbl):
            w.bind("<Button-1>", on_click)
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)

        sidebar_boutons[annee] = item


# ----------------------------------------------------------------------
#  Contenu principal (tableau de l'année sélectionnée)
# ----------------------------------------------------------------------

def selectionner_annee(annee):
    global annee_courante
    annee_courante = annee
    construire_sidebar()
    construire_contenu_principal()


def construire_contenu_principal():
    global tree

    for widget in zone_contenu.winfo_children():
        widget.destroy()

    if annee_courante is None:
        tk.Label(zone_contenu, text="Aucune année. Cliquez sur « Nouvelle année » pour commencer.",
                  font=(FONT_FAMILY, 12), bg=BG_MAIN, fg=TEXT_MUTED).pack(pady=60)
        return

    # ---- Barre supérieure : titre ----
    barre_haute = tk.Frame(zone_contenu, bg=BG_MAIN)
    barre_haute.pack(fill="x", padx=30, pady=(24, 16))

    titres_frame = tk.Frame(barre_haute, bg=BG_MAIN)
    titres_frame.pack(side="left")

    tk.Label(titres_frame, text=f"Registre {annee_courante}",
              font=(FONT_FAMILY, 18, "bold"), bg=BG_MAIN, fg=TEXT_DARK).pack(anchor="w")
    tk.Label(titres_frame, text=NOM_SERVICE,
              font=(FONT_FAMILY, 10), bg=BG_MAIN, fg=TEXT_MUTED).pack(anchor="w")

    tk.Label(barre_haute, text="💡 Double-cliquez sur « Nom », « Prénom » ou « Numéro de Fiche »\npour saisir ou modifier une valeur.",
              font=(FONT_FAMILY, 9, "italic"), bg=BG_MAIN, fg=TEXT_MUTED, justify="right").pack(side="right")

    # ---- Carte contenant le tableau ----
    carte = tk.Frame(zone_contenu, bg=CARD_BG, highlightthickness=1, highlightbackground=BORDER)
    carte.pack(fill="both", expand=True, padx=30, pady=(0, 24))

    colonnes = ("numero_dossier", "nom", "prenom", "numero_fiche")
    tree = ttk.Treeview(carte, columns=colonnes, show="headings", style="Moderne.Treeview")
    tree.heading("numero_dossier", text="NUMÉRO DE DOSSIER")
    tree.heading("nom", text="NOM")
    tree.heading("prenom", text="PRÉNOM")
    tree.heading("numero_fiche", text="NUMÉRO DE FICHE")
    tree.column("numero_dossier", width=160, anchor="center")
    tree.column("nom", width=220, anchor="w")
    tree.column("prenom", width=220, anchor="w")
    tree.column("numero_fiche", width=160, anchor="center")

    tree.tag_configure("oddrow", background=ROW_ALT)
    tree.tag_configure("evenrow", background=CARD_BG)

    scrollbar_y = ttk.Scrollbar(carte, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar_y.set)

    tree.pack(side="left", fill="both", expand=True, padx=(1, 0), pady=1)
    scrollbar_y.pack(side="right", fill="y", pady=1, padx=(0, 1))

    tree.bind("<Double-1>", modifier_cellule)

    charger_donnees(annee_courante)


def charger_donnees(annee):
    if tree is None:
        return
    for item in tree.get_children():
        tree.delete(item)

    cursor.execute('''
        SELECT id, nom, prenom, numero_fiche, numero_dossier
        FROM registre WHERE annee = ?
        ORDER BY LENGTH(numero_dossier), numero_dossier
    ''', (annee,))

    lignes = cursor.fetchall()
    for i, row in enumerate(lignes):
        ligne_id, nom, prenom, numero_fiche, numero_dossier = row
        tag = "evenrow" if i % 2 == 0 else "oddrow"
        tree.insert("", "end", iid=str(ligne_id),
                    values=(numero_dossier or "—", nom or "—", prenom or "—", numero_fiche or "—"), tags=(tag,))

    if not lignes:
        tk.Label(zone_contenu, text="Aucune donnée pour cette année.",
                  font=(FONT_FAMILY, 11), bg=BG_MAIN, fg=TEXT_MUTED).pack(pady=20)


# ----------------------------------------------------------------------
#  Édition directe dans le tableau (double-clic sur une cellule)
# ----------------------------------------------------------------------

def modifier_cellule(event):
    if tree is None:
        return
    region = tree.identify("region", event.x, event.y)
    if region != "cell":
        return

    row_id = tree.identify_row(event.y)
    col = tree.identify_column(event.x)  # '#1', '#2', '#3', '#4'
    if not row_id or not row_id.isdigit():
        return

    colonnes = ("numero_dossier", "nom", "prenom", "numero_fiche")
    try:
        col_index = int(col.replace("#", "")) - 1
        col_name = colonnes[col_index]
    except (ValueError, IndexError):
        return

    # Le numéro de dossier est attribué automatiquement : non modifiable ici
    if col_name == "numero_dossier":
        return

    bbox = tree.bbox(row_id, col)
    if not bbox:
        return
    x, y, width, height = bbox

    valeur_actuelle = tree.set(row_id, col_name)
    if valeur_actuelle == "—":
        valeur_actuelle = ""

    edit_entry = tk.Entry(tree, font=(FONT_FAMILY, 11), relief="flat",
                           highlightthickness=1, highlightbackground=ACCENT,
                           highlightcolor=ACCENT, bg="white", fg=TEXT_DARK)
    edit_entry.insert(0, valeur_actuelle)
    edit_entry.select_range(0, tk.END)
    edit_entry.place(x=x, y=y, width=width, height=height)
    edit_entry.focus()

    def sauvegarder(evt=None):
        if not edit_entry.winfo_exists():
            return
        nouvelle_valeur = edit_entry.get().strip()
        edit_entry.destroy()
        enregistrer_valeur_cellule(row_id, col_name, nouvelle_valeur)

    def annuler(evt=None):
        if edit_entry.winfo_exists():
            edit_entry.destroy()

    edit_entry.bind("<Return>", sauvegarder)
    edit_entry.bind("<FocusOut>", sauvegarder)
    edit_entry.bind("<Escape>", annuler)


def enregistrer_valeur_cellule(ligne_id, col_name, valeur):
    # Chaîne vide -> NULL en base, indispensable pour numero_fiche
    # (l'index unique autorise plusieurs NULL, mais pas plusieurs "").
    valeur_db = valeur if valeur != "" else None

    if col_name == "numero_fiche" and valeur:
        cursor.execute(
            "SELECT nom, prenom FROM registre WHERE numero_fiche = ? AND annee = ? AND id != ?",
            (valeur, annee_courante, ligne_id)
        )
        conflit = cursor.fetchone()
        if conflit:
            nom_conflit = " ".join(p for p in conflit if p) or "un autre patient"
            afficher_erreur(
                "Numéro de fiche déjà utilisé",
                f"Le numéro de fiche « {valeur} » est déjà attribué à "
                f"{nom_conflit} pour l'année {annee_courante}."
            )
            charger_donnees(annee_courante)
            return

    try:
        if col_name in ("nom", "prenom"):
            cursor.execute(f"UPDATE registre SET {col_name} = ? WHERE id = ?",
                            (valeur, ligne_id))
        else:
            cursor.execute("UPDATE registre SET numero_fiche = ? WHERE id = ?",
                            (valeur_db, ligne_id))
        conn.commit()
        charger_donnees(annee_courante)
    except sqlite3.IntegrityError:
        afficher_erreur("Doublon détecté", "Cette valeur est déjà utilisée par un autre patient.")
        charger_donnees(annee_courante)
    except sqlite3.Error as e:
        afficher_erreur("Erreur de base de données", str(e))


# ----------------------------------------------------------------------
#  Gestion des années (création + pré-remplissage automatique)
# ----------------------------------------------------------------------

onglets_annees = set()


def demander_nouvelle_annee():
    win = tk.Toplevel(root)
    configurer_fenetre_secondaire(win, "Nouvelle année", largeur=380)
    corps = win.corps

    entry = champ_formulaire(corps, "Année (AAAA)", row=1)
    entry.focus()


    def valider():
        annee = entry.get().strip()
        if not valider_annee(annee):
            afficher_erreur("Erreur", "Veuillez entrer une année valide (format : AAAA).")
            return
        if annee in onglets_annees:
            afficher_erreur("Année déjà existante", f"L'année {annee} existe déjà.")
            return

        try:
            lignes = [(annee, "", "", None, str(i)) for i in range(1, NOMBRE_DOSSIERS_AUTO + 1)]
            cursor.executemany('''
                INSERT INTO registre (annee, nom, prenom, numero_fiche, numero_dossier)
                VALUES (?, ?, ?, ?, ?)
            ''', lignes)
            conn.commit()
        except sqlite3.Error as e:
            afficher_erreur("Erreur de base de données", str(e))
            return

        onglets_annees.add(annee)
        win.destroy()
        selectionner_annee(annee)

    bouton_stylise(corps, "Créer l'année", valider, bg=ACCENT, hover=ACCENT_HOVER
                   ).grid(row=3, column=0, pady=22, padx=25, sticky="e")
    win.bind("<Return>", lambda e: valider())
    finaliser_fenetre(win)


# ----------------------------------------------------------------------
#  Recherche globale (toutes années confondues)
# ----------------------------------------------------------------------

def lancer_recherche_globale(event=None):
    terme = recherche_globale_entry.get().strip()
    if not terme:
        afficher_erreur("Recherche", "Veuillez saisir un nom ou prénom à rechercher.")
        return
    rechercher_patient_global(terme)


def rechercher_patient_global(terme):
    cursor.execute('''
        SELECT annee, id, numero_dossier, nom, prenom, numero_fiche
        FROM registre
        WHERE (nom LIKE ? OR prenom LIKE ?)
          AND ((nom IS NOT NULL AND nom != '') OR (prenom IS NOT NULL AND prenom != ''))
        ORDER BY annee DESC, LENGTH(numero_dossier), numero_dossier
    ''', (f"%{terme}%", f"%{terme}%"))
    resultats = cursor.fetchall()
    afficher_resultats_recherche(resultats, terme)


def afficher_resultats_recherche(resultats, terme):
    global tree
    for widget in zone_contenu.winfo_children():
        widget.destroy()
    tree = None

    barre_haute = tk.Frame(zone_contenu, bg=BG_MAIN)
    barre_haute.pack(fill="x", padx=30, pady=(24, 16))

    titres_frame = tk.Frame(barre_haute, bg=BG_MAIN)
    titres_frame.pack(side="left")
    tk.Label(titres_frame, text=f"Résultats pour « {terme} »",
              font=(FONT_FAMILY, 18, "bold"), bg=BG_MAIN, fg=TEXT_DARK).pack(anchor="w")
    tk.Label(titres_frame, text=f"{len(resultats)} résultat(s) — toutes années confondues",
              font=(FONT_FAMILY, 10), bg=BG_MAIN, fg=TEXT_MUTED).pack(anchor="w")

    bouton_stylise(barre_haute, "←  Retour", retour_depuis_recherche,
                   bg=TEXT_MUTED, hover=TEXT_DARK).pack(side="right")

    carte = tk.Frame(zone_contenu, bg=CARD_BG, highlightthickness=1, highlightbackground=BORDER)
    carte.pack(fill="both", expand=True, padx=30, pady=(0, 8))

    colonnes = ("annee", "numero_dossier", "nom", "prenom", "numero_fiche")
    resultats_tree = ttk.Treeview(carte, columns=colonnes, show="headings", style="Moderne.Treeview")
    resultats_tree.heading("annee", text="ANNÉE")
    resultats_tree.heading("numero_dossier", text="NUMÉRO DE DOSSIER")
    resultats_tree.heading("nom", text="NOM")
    resultats_tree.heading("prenom", text="PRÉNOM")
    resultats_tree.heading("numero_fiche", text="NUMÉRO DE FICHE")
    resultats_tree.column("annee", width=90, anchor="center")
    resultats_tree.column("numero_dossier", width=160, anchor="center")
    resultats_tree.column("nom", width=200, anchor="w")
    resultats_tree.column("prenom", width=200, anchor="w")
    resultats_tree.column("numero_fiche", width=160, anchor="center")

    resultats_tree.tag_configure("oddrow", background=ROW_ALT)
    resultats_tree.tag_configure("evenrow", background=CARD_BG)

    scrollbar_y = ttk.Scrollbar(carte, orient="vertical", command=resultats_tree.yview)
    resultats_tree.configure(yscrollcommand=scrollbar_y.set)
    resultats_tree.pack(side="left", fill="both", expand=True, padx=(1, 0), pady=1)
    scrollbar_y.pack(side="right", fill="y", pady=1, padx=(0, 1))

    if not resultats:
        tk.Label(carte, text="Aucun patient trouvé pour cette recherche.",
                  font=(FONT_FAMILY, 11), bg=CARD_BG, fg=TEXT_MUTED).pack(pady=40)
    else:
        for i, (annee, ligne_id, numero_dossier, nom, prenom, numero_fiche) in enumerate(resultats):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            resultats_tree.insert("", "end", iid=f"{annee}:{ligne_id}",
                                   values=(annee, numero_dossier or "—", nom or "—", prenom or "—", numero_fiche or "—"),
                                   tags=(tag,))

    def ouvrir_resultat(event):
        selection = resultats_tree.selection()
        if not selection:
            return
        annee_sel, ligne_id_sel = selection[0].split(":", 1)
        naviguer_vers_resultat(annee_sel, ligne_id_sel)

    resultats_tree.bind("<Double-1>", ouvrir_resultat)

    tk.Label(zone_contenu, text="Double-cliquez sur un résultat pour l'ouvrir dans son année.",
              font=(FONT_FAMILY, 9, "italic"), bg=BG_MAIN, fg=TEXT_MUTED).pack(anchor="w", padx=34)


def retour_depuis_recherche():
    if annee_courante:
        construire_contenu_principal()
    else:
        for widget in zone_contenu.winfo_children():
            widget.destroy()


def naviguer_vers_resultat(annee_sel, ligne_id_sel):
    global annee_courante
    annee_courante = annee_sel
    construire_sidebar()
    construire_contenu_principal()
    if tree is not None and tree.exists(ligne_id_sel):
        tree.selection_set(ligne_id_sel)
        tree.see(ligne_id_sel)
        tree.focus(ligne_id_sel)


# ----------------------------------------------------------------------
#  Fenêtre principale
# ----------------------------------------------------------------------
root = tk.Tk()
root.title(f"Registre Annuel — {NOM_SERVICE}")
root.geometry("1200x720")
root.configure(bg=BG_MAIN)
root.state('zoomed')

style = ttk.Style()
style.theme_use("clam")
style.configure("Moderne.Treeview", background=CARD_BG, fieldbackground=CARD_BG,
                foreground=TEXT_DARK, rowheight=38, font=(FONT_FAMILY, 18), borderwidth=0)
style.configure("Moderne.Treeview.Heading", background=ACCENT, foreground="white",
                font=(FONT_FAMILY, 10, "bold"), borderwidth=0, relief="flat")
style.map("Moderne.Treeview.Heading", background=[("active", ACCENT)])
style.map("Moderne.Treeview", background=[("selected", ACCENT_LIGHT)],
          foreground=[("selected", TEXT_DARK)])
style.layout("Moderne.Treeview", [('Moderne.Treeview.treearea', {'sticky': 'nswe'})])

# ---- En-tête (haut de page) ----
entete = tk.Frame(root, bg=SIDEBAR_BG, height=68)
entete.pack(fill="x", side="top")
entete.pack_propagate(False)

entete_textes = tk.Frame(entete, bg=SIDEBAR_BG)
entete_textes.pack(side="left", padx=24, pady=8)

tk.Label(entete_textes, text="📋  Registre Annuel", font=(FONT_FAMILY, 15, "bold"),
          bg=SIDEBAR_BG, fg="white").pack(anchor="w")
tk.Label(entete_textes, text=NOM_SERVICE, font=(FONT_FAMILY, 10),
          bg=SIDEBAR_BG, fg="#94A3B8").pack(anchor="w")

# ---- Recherche globale (toutes années) dans l'en-tête ----
entete_recherche = tk.Frame(entete, bg=SIDEBAR_BG)
entete_recherche.pack(side="right", padx=24)

recherche_globale_entry = tk.Entry(entete_recherche, font=(FONT_FAMILY, 11), relief="flat",
                                    bd=6, width=26, bg="white", fg=TEXT_DARK)
recherche_globale_entry.pack(side="left", padx=(0, 8), ipady=5)
recherche_globale_entry.bind("<Return>", lancer_recherche_globale)

bouton_stylise(entete_recherche, "🔍 Rechercher un patient", lancer_recherche_globale,
               bg=ACCENT, hover=ACCENT_HOVER, padx=14, pady=8, font_size=9).pack(side="left")

# ---- Corps : sidebar + contenu ----
corps = tk.Frame(root, bg=BG_MAIN)
corps.pack(fill="both", expand=True)

sidebar = tk.Frame(corps, bg=SIDEBAR_BG, width=220)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

tk.Label(sidebar, text="ANNÉES", font=(FONT_FAMILY, 9, "bold"), bg=SIDEBAR_BG,
          fg="#64748B", anchor="w", padx=16, pady=14).pack(fill="x")

sidebar_liste = tk.Frame(sidebar, bg=SIDEBAR_BG)
sidebar_liste.pack(fill="x")

sidebar_spacer = tk.Frame(sidebar, bg=SIDEBAR_BG)
sidebar_spacer.pack(fill="both", expand=True)

bouton_nouvelle_annee = bouton_stylise(sidebar, "＋  Nouvelle année", demander_nouvelle_annee,
                                        bg=ACCENT, hover=ACCENT_HOVER, padx=10, pady=10)
bouton_nouvelle_annee.pack(fill="x", padx=14, pady=16, side="bottom")

zone_contenu = tk.Frame(corps, bg=BG_MAIN)
zone_contenu.pack(side="left", fill="both", expand=True)

# ---- Initialisation des données ----
annees_existantes = lister_annees_existantes()
onglets_annees.update(annees_existantes)

if onglets_annees:
    construire_sidebar()
    selectionner_annee(sorted(onglets_annees, reverse=True)[0])
else:
    construire_sidebar()
    construire_contenu_principal()


def on_closing():
    conn.close()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()
