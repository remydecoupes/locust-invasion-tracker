#!/usr/bin/env python3
"""
Map Generator 
Folium map 
"""

import json
import os
from datetime import datetime
import folium
from folium.plugins import MarkerCluster, TimestampedGeoJson
from typing import List, Dict


class MapGenerator:
    def __init__(self):
        self.data_dir = "data"
        self.docs_dir = "docs"
        self.entities_file = os.path.join(self.data_dir, "entities.json")
        self.map_file = os.path.join(self.docs_dir, "index.html")
        
        # Madagascar coordinates (centroid)
        self.madagascar_center = [-18.8792, 47.5079]
        self.default_zoom = 6
    
    def load_entities(self) -> List[Dict]:
        """Load entities GPS"""
        if not os.path.exists(self.entities_file):
            print(f" [error] file {self.entities_file} not found")
            return []
        
        with open(self.entities_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def parse_date(self, date_str: str):
        """Convertit une date RSS (ex: Wed, 12 Jun 2024 07:00:00 GMT) en ISO"""
        if not date_str or date_str == "N/A":
            return None
        try:
            dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S GMT")
            return dt.isoformat()
        except Exception as e:
            print(f"⚠️  Date invalide: {date_str} ({e})")
            return None
    
    def create_popup_html(self, article: Dict, location: Dict) -> str:
        """Create HTML"""
        return f"""
        <div style="width: 300px; font-family: Arial, sans-serif;">
            <h4 style="margin: 0 0 10px 0; color: #d32f2f;">🦗 {article['title']}</h4>
            <p style="margin: 5px 0; font-size: 12px; color: #666;">
                <strong>📍 Lieu:</strong> {location['name']}<br>
                <strong>📅 Date:</strong> {article.get('published', 'N/A')}<br>
                <strong>📰 Source:</strong> {article.get('source', 'N/A')}
            </p>
            <p style="margin: 10px 0; font-size: 13px;">
                {article['summary'][:200]}...
            </p>

            <!-- 
            Lien vers l'article complet désactivé volontairement :
            - Problème d'accès aux flux Google News (erreur "Ce flux n'est pas disponible")
            - Risque de blocage CORS / restrictions Google
            - À réactiver si source API officielle ou liens directs médias
            -->
            <!--
            <a href="{article['link']}" target="_blank" 
               style="color: #1976d2; text-decoration: none; font-weight: bold;">
                📖 Lire l'article complet →
            </a>
            -->
        </div>
        """


    def generate_map(self, entities_data: List[Dict]) -> folium.Map:
        """Folium map"""
        print("  Map generation...")
        
        # Créer la carte centrée sur Madagascar
        m = folium.Map(
            location=self.madagascar_center,
            zoom_start=self.default_zoom,
            tiles='OpenStreetMap'
        )
        
        # Ajouter un titre
        title_html = '''
        <div style="position: fixed; 
                    top: 10px; left: 50px; width: 500px; height: 90px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:16px; padding: 10px; border-radius: 5px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
            <h3 style="margin: 0; color: #d32f2f;">🦗 Invasion de Criquets à Madagascar</h3>
            <p style="margin: 5px 0; font-size: 13px;">
                Surveillance des articles de presse via Google News RSS<br>
                <em>Dernière mise à jour: {}</em>
            </p>
        </div>
        '''.format(datetime.now().strftime("%Y-%m-%d %H:%M"))
        
        m.get_root().html.add_child(folium.Element(title_html))
        
        # Créer un cluster de marqueurs pour mieux gérer les lieux proches

        # old marker
        """
        marker_cluster = MarkerCluster(name="Articles").add_to(m)
        
        
        # Compteur de marqueurs
        marker_count = 0
        
        # Ajouter les marqueurs pour chaque article/lieu
        for item in entities_data:
            article = item['article']
            locations = item['locations']
            
            for location in locations:
                # Créer le popup
                popup_html = self.create_popup_html(article, location)
                popup = folium.Popup(popup_html, max_width=350)
                
                # Créer le marqueur
                folium.Marker(
                    location=[location['latitude'], location['longitude']],
                    popup=popup,
                    tooltip=f"{location['name']}: {article['title'][:50]}...",
                    icon=folium.Icon(color='red', icon='warning-sign', prefix='glyphicon')
                ).add_to(marker_cluster)
                
                marker_count += 1
        
        print(f"   ✅ {marker_count} marqueurs ajoutés")
        """

        # new marker with time management:
        features = []

        for item in entities_data:
            article = item['article']
            locations = item['locations']

            article_time = self.parse_date(article.get("published"))

            if not article_time:
                continue

            for location in locations:
                popup_html = self.create_popup_html(article, location)

                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [location['longitude'], location['latitude']],
                    },
                    "properties": {
                        "time": article_time,
                        "popup": popup_html,
                        "tooltip": f"{location['name']}: {article['title'][:50]}...",
                        "icon": "circle",
                        "iconstyle": {
                            "fillColor": "red",
                            "fillOpacity": 0.8,
                            "stroke": "true",
                            "radius": 6
                        },
                    },
                }

                features.append(feature)

        print(f"   ✅ {len(features)} points temporels ajoutés")

        TimestampedGeoJson(
            {
                "type": "FeatureCollection",
                "features": features,
            },
            period="P1D",              # Pas de temps = 1 jour
            add_last_point=True,
            auto_play=False,
            loop=False,
            max_speed=1,
            loop_button=True,
            date_options="YYYY-MM-DD",
            time_slider_drag_update=True,
        ).add_to(m)


        # Ajouter un layer control
        folium.LayerControl().add_to(m)
        
        return m
    
    def save_map(self, map_obj: folium.Map):
        """Sauvegarde la carte en HTML"""
        os.makedirs(self.docs_dir, exist_ok=True)
        
        map_obj.save(self.map_file)
        print(f"💾 Carte sauvegardée: {self.map_file}")
    
    
    def run(self):
        """Exécute la génération complète de la carte"""
        print("=" * 60)
        print("🗺️  MAP GENERATOR - VISUALISATION CARTOGRAPHIQUE")
        print("=" * 60)
        
        # Charger les entités
        entities_data = self.load_entities()
        
        if not entities_data:
            print("⚠️  Aucune donnée à visualiser")
            return
        
        # Filtrer uniquement les articles avec des localisations
        entities_with_locations = [item for item in entities_data if item['locations']]
        
        if not entities_with_locations:
            print("⚠️  Aucun article avec localisation trouvé")
            return
        
        print(f"📍 {len(entities_with_locations)} articles avec localisation")
        
        # Générer la carte
        map_obj = self.generate_map(entities_with_locations)
        
        # Sauvegarder
        self.save_map(map_obj)
        
        print("\n" + "=" * 60)
        print("✅ Carte générée avec succès!")
        print(f"   - Fichier: {self.map_file}")
        print(f"   - Pour visualiser: ouvrir dans un navigateur")
        print("=" * 60)


if __name__ == "__main__":
    generator = MapGenerator()
    generator.run()