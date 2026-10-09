import time
import requests
from pyVinted import Vinted

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = "8961529243:AAG6TKTS4XEj8Mhg91cpZH0f5zBabUR6zfs"
TELEGRAM_CHAT_ID = "7826082913"

# Recherche Vinted ciblée sur Jirachi, triée par nouveautés
VINTED_SEARCH_URL = (
    "https://www.vinted.fr/catalog?search_text=carte%20pokemon%20jirachi&order=newest_first"
)

# Mots-clés pour repérer une carte en état parfait (potentiel PSA 10)
PSA10_KEYWORDS = [
    "neuf", "packfresh", "pack fresh", "mint", "near mint",
    "nm", "booster", "sleeve", "protege", "impeccable", "gem", "parfait"
]

CHECK_INTERVAL = 60  # Fréquence de vérification en secondes

vinted = Vinted()
seen_item_ids = set()


def is_potential_psa10(title, description=""):
    """Vérifie si l'annonce contient des termes indiquant un état impecable."""
    text = f"{title} {description}".lower()
    return any(keyword in text for keyword in PSA10_KEYWORDS)


def send_telegram_notification(title, price, url, photo_url=""):
    """Envoie le message formaté sur ton Telegram."""
    message = (
        f"⭐ <b>Jirachi détecté (Potentiel PSA 10) !</b>\n\n"
        f"📌 <b>Titre :</b> {title}\n"
        f"💰 <b>Prix :</b> {price} €\n\n"
        f"🔗 <a href='{url}'>Voir l'annonce Vinted</a>"
    )

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }

    if photo_url:
        payload["photo"] = photo_url
        payload["caption"] = message
        endpoint = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    else:
        payload["text"] = message
        endpoint = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    try:
        response = requests.post(endpoint, data=payload, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Erreur d'envoi Telegram : {e}")


def check_vinted():
    """Scrape la recherche Vinted et avertit en cas de nouveauté."""
    global seen_item_ids
    print("Vérification Vinted en cours...")

    try:
        items = vinted.items.search(VINTED_SEARCH_URL, 10, 1)

        # Premier lancement : mémorisation des cartes actuelles pour ne pas spamer
        if not seen_item_ids:
            for item in items:
                seen_item_ids.add(item.id)
            print(f"Initialisation : {len(seen_item_ids)} annonces Jirachi mémorisées.")
            return

        # Traitement des nouvelles annonces
        for item in reversed(items):
            if item.id not in seen_item_ids:
                seen_item_ids.add(item.id)

                title = item.title
                description = getattr(item, "description", "")
                price = item.price
                url = item.url
                photo = item.photo if hasattr(item, "photo") else ""

                if is_potential_psa10(title, description):
                    print(f"[ALERTE SENT] {title} - {price}€")
                    send_telegram_notification(title, price, url, photo)
                else:
                    print(f"[IGNORÉ - Pas assez neuf] {title}")

    except Exception as e:
        print(f"Erreur lors de la vérification Vinted : {e}")


if __name__ == "__main__":
    print("Démarrage du bot Jirachi PSA 10...")
    # Test d'envoi initial pour valider le fonctionnement de Telegram
    send_telegram_notification("Test du Bot", "0", "https://www.vinted.fr")
    print("Message de test envoyé sur Telegram !")

    while True:
        check_vinted()
        time.sleep(CHECK_INTERVAL)
