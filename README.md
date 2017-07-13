# field-campaigner

This repository is the starting point for upcoming work focused on organizing field mapping at scale.  

Join the development: 

  * Add to the discussion in the [issue tracker](https://github.com/hotosm/field-campaigner/issues). Tag issues as Discussion or Ideas to contribute. 
  * More information and project documentation about the vision and scope in the [wiki](https://github.com/hotosm/field-campaigner/wiki)
  * Join online chat on [HOT’s Slack community](https://hotosm-slack.herokuapp.com/), #field-campaigner channel. 
  
  <img src="https://hotosm-slack.herokuapp.com/badge.svg">

# Project Overview

This project is based on the original work done in the osm-reporter. The project was extended to include a campaign management application. The aim of the campaign management is to allow field campaigns to be tracked and their quality measured. 

## OSM Users

The OSM user identity is used in this project. All actions are performed as such. A list of authorized admin users is maintained in the settings file. 

# How to build field-campaigner

Go to /osm-reporter/deployment
```
make build
make run
```

For testing, please for in the .modules file, and edit .modules file to your repo.

# User Interface

## Starting a Campaign

Authorized users may start a campaign. This is done by selecting the “Add Campaign” button on the Landing Page.

A campaign has standard attributes, such as boundaries, start and end dates as well as name and description. The campaign progress is obtained through insights functions, which are broken up into classes. These insights functions take data from a data source, such as the OSM reporter, and convert them to quantifiable insights. The campaign manager selects which insights functions best meet the requirements of this campaign.

## Viewing a Campaign

The Campaign Dashboard Page shows the default attributes as well as the UI component of the Insights Function. Alongside the UI component each of the insights functions provide additional details on how these insights where obtained. These additional details may are shown if the user explodes the hyperlink with this information.

## Editing a Campaign

A campaign is edited in the same view as it is created. As such this is not a very different experience.

# Technical Details

The insights functions are clearly understandable english sentences, which highlight an analytical goal. Some additional parameters may be given, but this is made clear when selecting this function. Under the hood there are two parts to this the first is the Data Provider, against which an Insights Function can be registered and the Insights Function itself.

## Data Provider

The Data Provider is an abstraction around the data source. External resource querying is handled here. The prime example is the OSM Reporter Function Provider, which provides the feature list over a given time period for a specific area. This data is aggregated here and passed on to the relevant insights functions. 

## Insights Function

The Insights Function takes data from a Data Provider and performs a calculation over this data. The output of this function is a UI component, for displaying on the dashboard, a detailed description of how this data was obtained and, where relevant, a set of links on where to view/correct these.
