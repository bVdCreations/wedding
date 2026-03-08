from pydantic import BaseModel


class WeddingConfig(BaseModel):
    couple_names: str = "Bastiaan & Gemma"
    ceremony_date: str = "November 7, 2026"
    ceremony_time: str = "12:00"
    venue_name: str = "Rancho del Inglés"
    venue_address: str = "Camino del Convento, s/n, 29130 Alhaurín de la Torre, Málaga, Spain"
    contact_email: str = "info@gemma-bastiaan.wedding"
    rsvp_deadline: str = "April 2, 2026"
    google_maps_url: str = "https://www.google.com/maps/dir/?api=1&destination=Rancho+del+Ingles,+Camino+del+Convento,+Alhaurin+de+la+Torre,+Malaga"
