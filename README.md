# Locust invasion Tracker - Madagascar

Display a map that plot articles metadata dealing with Locust invasion.

## Pipeline: 
1. Source of data: Google News aggregator (RSS flux)
2. Filter only relevant articles based on the keyword list: 
```{python}
["criquet", "criquets", "locust", "locusts", "acridien", "essaim"]
```
3. With SpaCy extract location found in Title/abstract of new article
4. Display on map