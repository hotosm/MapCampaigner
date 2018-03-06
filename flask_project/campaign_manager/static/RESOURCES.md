# Map Campaigner
<br>
<br>

**Contents**

**Section 1 - General Information Page**

- --Starting a campaign
- --Setting a campaign start and end date
- --Describing campaign
- --Campaign type
- --Setting campaign managers
- --Additional options

**Section 2 - Campaign AOI**

- --Defining an AOI by digitising the map
- --Defining an AOI by uploading a shapefile
- --Defining an AOI by creating a GeoJSON file
- --Labelling and assigning campaign area

**Section 3 - Remote Mapping**

**Section 4 - Submitting and Editing a Campaign**

To get started with your new campaign simply click on the &#39;Create a Campaign&#39; link from the top-right hand corner of the homepage next to your username.
<br><br>
![Monitor Mapping](static/img/resources-1.png)
<br><br>

**General Information Page**

The first section you will be taken to is the &#39;General Information&#39; page. In this section you will be able to set a name for you campaign, a start and end date, and define the type of campaign and features to be collected for the campaign.

**Campaign Start and End date**

The start date of the campaign should be the date that you want the campaign to become &#39;active&#39; for field mappers to begin data collection. The end date is when you want all of the specified data to have been collected.
<br><br>
![Monitor Mapping](static/img/resources-2.png)
<br><br>

_Start and End campaign date display_

When a campaign is &#39;active&#39; it will preview on the main Map Campaign homepage and the AOI will appear as a pin on the map tile. Before the start date, the campaign you have created will be listed as &#39;inactive&#39;. After the start date, your campaign will be listed as &#39;running&#39;. Once the end date has been reached, this will change to &#39;finished&#39;.
<br><br>
![Test Campaign](static/img/resources-3.png)
<br>
_Active campaign dashboard display_
<br><br>
![Lisbon Test](static/img/resources-4.png)
<br>
_Finished campaign dashboard display_

Note: You can edit the end date of your campaign at any time, for example if a project is extended and additional data needs to be collected.

**Description**

In the description section you should provide a detailed explanation of the campaign objective. This should include the area of interest, the key features to be collected, and any other information you can provide on the utilisation of this data.

For example:

_This is Phase 2 of the Map Yumwe Camp campaign. The aim of this project is to collect data on the water points across the Yumbwe Camp in Uganda. This data will be used by local NGOs for camp improvements and future planning._

**Campaign Type**

This section allows you to define the type of data to be collected by field teams. You can select from editable campaign types by clicking, &#39;Choose a template&#39;, which lists a set of common features e.g. buildings, toilets etc. You can add multiple feature templates to your campaign by continuing to click the &#39;Choose a template&#39; button. A set of common tags associated with each feature have been preloaded. Once you have selected the key features of your campaign, you can edit the tags you need for each feature. Tags can be removed by pressing the &#39;x&#39; button next to each tag. Additional tags can be added by clicking on the &#39;+Add&#39; button underneath the tag column. A drop-down list of tag suggestions will appear which can then be selected and added to the feature.
<br><br>
![Adding and editing campaign features from a template](static/img/resources-5.png)
<br>
_Adding and editing campaign features from a template_

To generate specific campaign features, click on the &#39;+Add custom tags&#39; button. This allows you to add define a specific feature and accompanying tags. Please make sure that custom features and tags still align with [OSM tagging standards](https://wiki.openstreetmap.org/wiki/Map_Features).
<br><br>
![Pop-up display to add custom campaign features](static/img/resources-6.png)
<br>
_Pop-up display to add custom campaign features_

**Managers**

As Campaign Creator, you will automatically be added as a Campaign Manager. You can add or remove Campaign Managers to a campaign by typing their OSM username into the box and searching.

Note: Campaign Managers are able to edit all features of the campaign, so these should be trusted individuals e.g. programme managers, field managers, team leads.

**Other Options**

_OpenMapKit_

To integrate OpenMapKit into your campaign, you can tick the &#39;Add button to integrate to OpenMapKit&#39; box. By ticking this box you will create a direct link for users to OpenMapKit from your campaign page. This allows field teams to open the AOI area directly onto their smartphones from the campaign project page.

_Custom Basemap_

This feature gives you the option to add custom basemap tiles by inputting the map url. Leave this section blank if you wish to use the default basemap.

**Campaign AOI**

This section allows you to define the Area of Interest for you campaign. You can set your AOI using three different methods: defining the campaign area by digitising the map, uploading a shapefile, or uploading a GeoJSON file.

**Option 1: Define Campaign Area**

You can set your AOI by using the map to zoom into the area you wish to select or by using the search function on the map sidebar. Once you have focused in on the area you want to select, you can set the boundaries for the AOI using the rectangle or polygon tool.

To use the rectangle tool, simply click to begin drawing the first corner of the rectangle and drag your cursor to the area you wish to define. Click to complete the rectangle.
<br><br>
![Using the Rectangle tool to define the AOI boundaries](static/img/resources-7.png)
<br>
_Using the Rectangle tool to define the AOI boundaries_

To use the polygon tool, simply click to start drawing the first point of your shape, click to continue drawing your shape, and then click the first point to close the shape.
<br><br>
![Using the polygon tool to define the AOI boundaries](static/img/resources-8.png)
<br>
_Using the polygon tool to define the AOI boundaries_

Note: If the area size of your AOI is too large, an error message will display and you will need to redraw the boundaries of your AOI. You can check the area size you have drawn by monitoring the &#39;Area size&#39; box at the bottom-left corner of the map. This box will display in red if the area size is too large and green when the area size is appropriate.

**Option 2 : Upload Shapefiles**

Map Campaigner gives you the option to upload shapefiles (.dbf, .shop, or .shx) to define your AOI. You can read more about different shapefile types on the LearnOSM website [here](http://learnosm.org/en/osm-data/file-formats/), and how to extract data into different file types [here](http://learnosm.org/en/osm-data/getting-data/).

**Option 3 : Creating a GeoJSON file**

You can create a GeoJSON file using the website [geojson.io](http://geojson.io/) and searching for the area you wish to define. Once you have zoomed into the correct area, there are similar tools you can use to draw the boundaries of the AOI, such as the rectangle and polygon tool. GeoJSON allows you to draw multiple shapes. Having multiple areas of an AOI can be useful for monitoring the data collection progress within certain areas of an AOI within Map Campaigner.
<br><br>
![GeoJSON file](static/img/resources-9.png)
<br><br>
Once you are happy with the area you have selected, you can save the file by clicking on the &#39;Save&#39; button from the top-left menu bar and selecting &#39;GeoJSON&#39;. This will save the file to your device.

In Map Campaigner, to upload your GeoJSON file, click the &#39;Upload GeoJSON File&#39; button, locate the file on your computer and click open.

**Labelling and Assigning Campaign Areas**

Once you have defined the campaign AOI, you have the option to label the area you have created and assign teams to a specific section. For example, if you have created a shapefile with

It is also three sections, you can assign three field teams for data collection in each section. As Campaign Manager, you can then monitor the progress of each team and mark each section as &#39;unassigned&#39;, &#39;incomplete&#39; or &#39;complete&#39; dependent on the progress of each team.
<img> <br><br>
![Create AOI](static/img/resources-10.png)
<br><br>
It is also useful to split up your AOI into smaller sections if you are collecting data across a large area. Since field teams may choose to collect data in specific areas on certain days, the data collection progress can be marked as &#39;complete&#39; as the campaign progresses.

**Remote Mapping**

If you have remote mapping projects which are relevant to your campaign, you can add these under the remote mapping section. This will allow you to monitor the progress of the remote campaign in correlation with the field data collection being undertaken.

You can search for your remote mapping project using the search functions under &#39;Search Project&#39;. You can search by project location, mapper level, mapping type, organisation tag, or campaign tag.

A list of tasking manager projects will display under your search. To select a project, simply click the green &#39;Add Project&#39; button under the correct project. A description of the project is pulled from the tasking manager description. You can add multiple projects to this section by repeating this process. You can remove a project by clicking the red &#39;Remove project&#39; button.
<br><br>
![Remote Mapping project monitoring](static/img/resources-11.png)
<br>_Remote Mapping project monitoring_

**Submitting and Editing your Campaign**

Once you have completed each section, you can submit your campaign by clicking the orange &#39;Submit/Update&#39; button at the bottom of the page. You can edit your campaign at any time by clicking the orange &#39;Manage&#39; button on your campaign page.

**Advanced Mode**

Advanced mode allows you to manually edit json.