from pydantic import BaseModel


class WeddingConfig(BaseModel):
    couple_names: str = "Bastiaan & Gemma"
    ceremony_date: str = "November 7, 2026"
    ceremony_time: str = "12:00"
    venue_name: str = "Rancho del Inglés"
    venue_address: str = "Camino del Convento, s/n, 29130 Alhaurín de la Torre, Málaga, Spain"
    reception_details: str = "Drinks & Appetizers → Wedding Lunch → Dancing & Celebration"
    contact_email: str = "info@gemma-bastiaan.wedding"
    rsvp_deadline: str = "September 7, 2026"
    google_maps_url: str = "https://www.google.com/maps/dir/?api=1&destination=Rancho+del+Ingles,+Camino+del+Convento,+Alhaurin+de+la+Torre,+Malaga"
