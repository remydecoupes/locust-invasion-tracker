# Locust invasion Tracker - Madagascar

Display a map that plot articles metadata dealing with Locust invasion.

## Pipeline 
1. Source of data: Google News aggregator (RSS flux)
2. Filter only relevant articles based on the keyword list: 
```{python}
["criquet", "criquets", "locust", "locusts", "acridien", "essaim"]
```
3. With SpaCy extract location found in Title/abstract of new article
4. Display on map

## See results

Connect to [[website](https://remydecoupes.github.io/locust-invasion-tracker/)]

<p align="center">
  <img src="img/map_illustration.png" width="400"/>
  <br>
  <em>Fig. 1 - Overview of the Madagascar map with localized articles</em>
</p>

## Improvements

- Map
    - Add time management
    - Deal with too global location (i.e. Madagascar)
- RSS parser 
    - Extract link to the article