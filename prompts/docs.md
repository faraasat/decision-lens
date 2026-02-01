https://docs.grid.gg/public/documentation/api-documentation
https://docs.grid.gg/public/documentation/api-documentation/getting-started/glossary
https://docs.grid.gg/public/documentation/api-documentation/static-data/data-feed-quick-start-guide
https://docs.grid.gg/public/documentation/api-documentation/static-data/central-data-feed-api-overview
https://docs.grid.gg/public/documentation/api-documentation/static-data/static-data-entities
https://docs.grid.gg/public/documentation/api-documentation/static-data/static-data-faq
https://docs.grid.gg/public/documentation/api-documentation/in-game-data/live-data-feed-quick-start-guide
https://docs.grid.gg/public/documentation/api-documentation/in-game-data/getting-data-for-a-series
https://docs.grid.gg/public/documentation/api-documentation/in-game-data/series-state
https://docs.grid.gg/public/documentation/api-documentation/in-game-data/series-events
https://docs.grid.gg/public/documentation/api-documentation/in-game-data/grid-file-download-api
https://docs.grid.gg/public/documentation/api-documentation/data-analysis/stats-feed-overview
https://docs.grid.gg/public/documentation/api-documentation/game-developers/overview
https://docs.grid.gg/public/documentation/api-documentation/game-developers/quick-start-guide
https://docs.grid.gg/public/documentation/api-documentation/game-developers/post-game-visualisations-overview
https://docs.grid.gg/public/documentation/api-reference/getting-started/overview
https://docs.grid.gg/public/documentation/api-reference/getting-started/authentication
https://docs.grid.gg/public/documentation/api-reference/getting-started/graphql
https://docs.grid.gg/public/documentation/api-reference/getting-started/websocket
https://docs.grid.gg/public/documentation/api-reference/central-data-feeds/central-data-feed-api
https://docs.grid.gg/public/documentation/api-reference/live-data-feed/api-reference-series-state-api
https://docs.grid.gg/public/documentation/api-reference/live-data-feed/series-events-api
https://docs.grid.gg/public/documentation/api-reference/live-data-feed/grid-file-download-reference
https://docs.grid.gg/public/documentation/api-reference/stats-feed/stats-feed-api
https://docs.grid.gg/public/documentation/video/getting-started/video-overview
https://docs.grid.gg/public/documentation/video/rtmp-video/rtmp-video-getting-started
https://docs.grid.gg/public/documentation/video/rtmp-video/rtmp-video-quick-start-guide
https://docs.grid.gg/public/documentation/video/hls-video/hls-video-getting-started
https://docs.grid.gg/public/documentation/video/hls-video/hls-video-quick-start-guide
https://docs.grid.gg/public/documentation/video/video-widget/video-widget-getting-started
https://docs.grid.gg/public/documentation/video/video-widget/video-widget-quick-start-guide
https://docs.grid.gg/public/documentation/graphql-playground

---

Authenticating Your API Requests
If you have encountered the dreaded 401 (unauthorized error), you might need some help figuring out the proper way to authenticate your API requests. Read on for the info you need!

There are two ways to authenticate your API requests. You can either pass the API key into your request as a header, or you can include it in the URL as a request parameter. Note that request headers are a better way to keep your API key secure than request parameters.

NOTE: If you don’t know your API key, ask the admin user for your team to find it in the Account Management > Users area. If you are the admin, you can find Account Management at the bottom of the left navigation bar. Click “View” on the appropriate user in the list, then click where it says “API Keys” to view that user’s API key.

Using Request Headers
Your API key can be sent as part of your request using an “x-api-key” header. See the examples below. In these examples, we are downloading the GRID-formatted end-state data for series ID 2589176.

Python
Below is an example API request, using the built-in requests module.


import requests

headers = {
"x-api-key": "YOUR_API_KEY"
}

response = requests.get(
"https://api.grid.gg/file-download/end-state/grid/series/2589176",
headers = headers
)
JavaScript
Below is an example API request in JavaScript, using the axios package.


const axios = require('axios');

axios.get('https://api.grid.gg/file-download/end-state/grid/series/2589176', {
headers: {
‘x-api-key’: ‘YOUR_API_KEY’
}
})
.then(response => {
// Interact with the response object as necessary
// The response body will be contained within response.data
});
Curl
You can use headers to authenticate a curl request as follows:



curl https://api.grid.gg/file-download/end-state/grid/series/2589176 -H "x-api-key: YOUR_API_KEY"

Minor variations in curl syntax may be necessary on different platforms (Linux vs. macOS vs. Windows).

Using Request Parameters
Your API key can also be sent using a URL parameter, though this is a less secure method. See the examples below. In these examples, we are downloading the GRID-formatted end-state data for series ID 2589176.

Python
Below is an example API request, using the built-in requests module.


import requests

response = requests.get(
"https://api.grid.gg/file-download/end-state/grid/series/2589176?key={YOUR_API_KEY}"
)
JavaScript
Below is an example API request in JavaScript, using the axios package.


const axios = require('axios');

axios.get(
'https://api.grid.gg/file-download/end-state/grid/series/2589176?key=YOUR_API_KEY'
).then(response => {
// Interact with the response object as necessary
// The response body will be contained within response.data
});
Curl
You can use a request parameter to authenticate a curl request as follows:



curl https://api.grid.gg/file-download/end-state/grid/series/2589176?key=YOUR_API_KEY

---

Fetching Lists of Series from the GRID API
Before you can fetch and use the in-game data for the matches available on the GRID Platform (for example, to download your scrim files if you belong to a professional team), you will need to find a list of series IDs for your code to work through. Here's how to get that list, using GRID's Central Data API.

Central Data is a GraphQL API that contains GRID's "static data", such as data about teams, players, tournaments, and series.

For details about how to work with GRID's GraphQL APIs, including details around pagination, rate limiting, and errors, see the GraphQL API Reference documentation.

Preparing and Sending Your Query
To get a list of series that meet certain criteria, we'll use the allSeries query.

Here's a basic example of a simple allSeries query that fetches the most recent 50 Valorant esports series.

In this example, we have used filters to request only VALORANT series and only "esports" series (no scrims).

Endpoint: https://api.grid.gg/central-data/graphql


{
allSeries (
first: 50,
filter: {
titleId: 6  # Valorant
types: ESPORTS  # Esports matches only
}
orderBy: StartTimeScheduled  # Sort by start time
orderDirection: DESC  # Sort by most recent first
) {
totalCount
pageInfo {
hasPreviousPage
hasNextPage
startCursor
endCursor
}
edges {
node {
id
title {
id
}
tournament {
id
name
}
}
}
}
}
Parameters and Filters in this Query
The first: 50 parameter specifies that we want to receive 50 results per page, which is the maximum allowed.

Filters


filter: {
titleId: 6
types: ESPORTS
}
The titleId: 6 portion requests the Valorant game title. See below for title IDs for other game titles.

The types: ESPORTS portion requests only esports series (no scrims).

Finally, orderBy: StartTimeScheduled sorts the response by start time, and orderDirection: DESC asks it so sort the most recent first (descending order).

Response Fields in this Query
The totalCount field asks the query to show us how many total series are available using these filters.


pageInfo {
hasPreviousPage
hasNextPage
startCursor
endCursor
}
These pagination fields give us useful information about which page we are viewing within all of the available pages of results. More on that later!


edges {
node {
id
tournament {
id
name
}
}
}
This portion of the query asks GraphQL to send us information about each series as an array of "nodes." For more on what "edges" and "nodes" are in GraphQL, see the official documentation.

Within each node, we are asking for the id of the series and the id and name of the tournament to which it belongs. Several other fields are available for series nodes, as listed here.

Filters
There are several different filters you can use to ensure that you are finding all of the series you are interested in, and only the series you are interested in.

To use a filter, simply add it on a line inside the filter: {} portion of your query. Some commonly useful filters are described below, with a complete list available here.

titleId

This filters the result by game title. For example, you can use these values:

VALORANT - 6
LOL - 3
Rainbow 6: Siege - 25
For a complete list of title IDs, see the API Reference.

types

Available series types include ESPORTS (official matches), SCRIM (private practice matches), and COMPETITIVE (Champions Queue).

startTimeScheduled The time the series was scheduled to begin, using UTC. To use this filter, you must provide either a gte paramter ("greater than or equal"), an lte paramater ("less than or equal"), or both. For example, to find series that started between January 1, 2023 and December 31, 2023, you could use this filter:


startTimeScheduled: {
gte: "2023-01-01T00:00:00Z"
lte: "2023-12-31T00:00:00Z"
}
productServiceLevels

This filter can restrict the results to only show games with certain levels of available data. For example, to only return series with complete live data, you could use this filter:


productServiceLevels: {
productName: "liveDataFeed"
serviceLevel: FULL
}
Pagination
Since you can only retrieve 50 records at a time, you may need to submit many queries to fetch a complete list of series that match your filters. You can do this using query pagination.

For a detailed guide to using pagination in your queries, see the GraphQL API Reference documentation.

---
