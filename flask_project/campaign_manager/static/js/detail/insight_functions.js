var activeInsightPanel = '';

function renderInsightFunctions(username) {

    renderRemoteProjects();

    $.each(selected_functions, function (key, selected_function) {

        var insightPanel = $('.advance-insights').clone()[0];
        var $insightPanel = $(insightPanel);
        $('.advance-insights-wrapper').append($insightPanel);
        $insightPanel.show();

        var $insightTitle = $insightPanel.find('.panel-heading');
        var $insightContent = $insightPanel.find('.panel-body');

        if (selected_function['name']) {
            var allow_function = true;
            if (selected_function['manager_only']) {
                if ($.inArray(username, managers) === -1) {
                    allow_function = false;
                }
            }
            if (allow_function) {
                var tab_id = key;
                var tab_name = selected_function['name']
                if(selected_function['feature']) {
                    tab_name += ' for ' + selected_function['feature'];
                }
                $insightTitle.html(tab_name);
                $insightContent.append(
                    '<div id="' + tab_id + '">' +
                        '<span class="grey-italic" style="margin-top:15px !important; position: absolute;"> Loading data .. </span>' +
                    '</div>'
                );
                getInsightFunctions(key);
                if (!containsObject(selected_function['feature'], feature_type_collected)) {
                    feature_type_collected.push(selected_function['feature']);
                }
            }
        }
    });

    for (var i = 0; i < feature_type_collected.length; i++) {
        calculateContributors(feature_type_collected[i]);
    }

}

function calculateCampaignProgress() {
    var $campaignStatus = $('.detail-campaign-status');
    var $campaignStatusLabel = $('.detail-campaign-status label');

    if (start_date === 'None' || end_date === 'None') {
        $('.detail-campaign-status label').html('-');
        return;
    }

    start_date = moment(start_date, 'YYYY-MM-DD', true);
    end_date = moment(end_date, 'YYYY-MM-DD', true);

    var campaign_range = end_date.diff(start_date, 'days') + 1; // Include start

    if (campaign_range < 0) {
        $campaignStatusLabel.html('-');
        return;
    }

    var remaining_days = end_date.diff(moment(), 'days') + 1;

    var progress = 0;

    if (remaining_days <= 0) {
        progress = 100;
        $campaignStatus.removeClass('running');
        $campaignStatus.addClass('finished');
        $campaignStatusLabel.html('Finished');
    } else {
        progress = 100 - (remaining_days / campaign_range * 100);
    }

    $('#campaign-progress').css({
        'width': progress + '%'
    })
}

function getInsightFunctions(function_id, type_id) {
    var url = '/campaign/' + uuid + '/' + function_id;
    var isFirstFunction = true;
    $.ajax({
        url: url,
        success: function (data) {
            var active = '';
            if (isFirstFunction) {
                active = 'active';
                isFirstFunction = false;
            }

            var $divFunction = $('#' + function_id);
            $divFunction.html(data);
            var $subContent = $divFunction.parent().next();
            if($divFunction.find('.table-insight-view').length > 0) {
                $subContent.html($divFunction.find('.table-insight-view'));
            }

            if($divFunction.find('.total-features').length > 0) {
                var value = parseInt($divFunction.find('.total-features').html());
                total_features_collected += value;
                $('#features-collected').html(total_features_collected);

                if(typeof type_id !== 'undefined') {
                    var $currentTypeFeatureCollected = $('#type-'+type_id + ' .features-collected');
                    var currentValue = parseInt($currentTypeFeatureCollected.html()) || 0;
                    var totalValue = currentValue + value;
                    $currentTypeFeatureCollected.html(totalValue);
                }
            }

            if($divFunction.find('.insight-summaries').length > 0) {
                if(typeof type_id !== 'undefined') {
                    $('#'+type_id+'-summaries').append($divFunction.find('.insight-summaries').html());
                }
            }
        }
    });
}

function renderInsightFunctionsTypes(username) {

    var campaignTypes = {};
    var $insightTabs = $('.insight-tabs');
    var $insightContent = $('.insight-content');
    var $insightFunctionPanel = $('.insight-function-panel');
    var index = 0;

    if (Object.keys(selected_functions).length === 0 && remote_projects.length === 0) {
        $insightFunctionPanel.html(
            '<h4 class="grey-italic">No insight Function</h4>'
        )
    } else {
        $insightTabs.show();
    }

    for (var key in campaign_types) {
        if (!campaign_types.hasOwnProperty(key)) {
            continue;
        }
        campaignTypes[campaign_types[key]['type']] = {};

        for(var selectedKey in selected_functions) {
            if(!selected_functions.hasOwnProperty(selectedKey)) {
                continue;
            }

            if(selected_functions[selectedKey]['type'] === campaign_types[key]['type']) {
                campaignTypes[campaign_types[key]['type']][selectedKey] =
                    selected_functions[selectedKey];
                delete selected_functions[selectedKey];
            }
        }
    }

    /***
    campaignTypes will contains this data:
    {"Educational Facilities":[
        {"function-2":{
            "function":"FeatureAttributeCompleteness",
            "category":"quality-function",
            "feature":"amenity=college,kindergarten,school,university",
            "attributes":"all",
            "type":"Educational Facilities",
            "type_required":"true",
            "manager_only":false,
            "name":"Showing feature completeness for Educational Facilities"}}]
    }
    ***/

    for (var campaignType in campaignTypes) {

        var tabName = campaignType;
        var tabId = tabName.replace(/\s+/g, '_');

        var active = '';
        if (index === 0) {
            active = 'active';
            activeInsightPanel = tabId;
        }

        $('.map-side-panel').append(
            '<div class="map-side-list map-side-type" id="type-'+tabId+'">'+
                '<div class="row">'+
                    '<div class="col-lg-10">'+
                        '<div class="pull-left map-side-list-name">'+
                                tabName +
                        '</div>'+
                        '<span class="pull-right map-side-list-number">'+
                                '<span class="features-collected">Loading data...</span>'+
                                '</span>'+
                    '</div>'+
                    '<div class="col-lg-2 map-side-list-action">'+
                        '<div class="side-action '+ active +'">'+
                            '<i class="fa fa-eye" aria-hidden="true" onclick="showInsightFunction(this, \''+tabId+'\')"></i>'+
                        '</div>'+
                    '</div>'+
                '</div>'+
                '<div id="'+tabId+'-summaries" class="side-panel-summaries"></div>'+
            '</div>'
        );

        $insightContent.find('#' + key).remove();
        $insightContent.append(
            '<div class="tab-pane fade ' + active + ' in" id="' + tabId + '"></div>'
        );

        var $typeContents = $('#'+tabId);

        $typeContents.append('<div class="row insight-type-content"></div>');
        $typeContents.append('<div class="row insight-type-sub-content"></div>');

        var $mainRowTypeContents = $('#'+tabId+ ' .insight-type-content');
        $mainRowTypeContents.append('<div class="type-title">'+tabName+'</div>');

        var insightIndex = 1;
        $.each(campaignTypes[campaignType], function (key, selected_function) {

            if (selected_function['name']) {
                var allow_function = true;
                if (selected_function['manager_only']) {
                    if ($.inArray(username, managers) === -1) {
                        allow_function = false;
                    }
                }
                if (allow_function) {
                    var insightId = key;
                    var sizeColumn = 'col-lg-4';

                    if(insightIndex % 3 === 0) {
                        sizeColumn = 'col-lg-4';
                    }

                    $mainRowTypeContents.append(
                            '<div class="'+sizeColumn+'" id="' + insightId + '">' +
                            '<span class="grey-italic" style="margin-top:15px !important; position: absolute;"> ' +
                                'Loading data .. </span>' +
                            '</div>'
                    );

                    getInsightFunctions(insightId, tabId);
                    if (!containsObject(selected_function['feature'], feature_type_collected)) {
                        feature_type_collected.push(selected_function['feature']);
                    }

                    insightIndex++;
                }
            }
        });

        index++;
    }

    renderInsightFunctions(username);
}

function showInsightFunction(element, tabId) {
    var $divParent = $(element).parent();
    map.fitBounds(drawnItems.getBounds());

    if($divParent.hasClass('active')) {

    } else {

        var $divParentActive = $('#type-'+activeInsightPanel + " .side-action");
        $divParentActive.removeClass('active');
        $divParent.addClass('active');

        $('#'+activeInsightPanel).hide();
        activeInsightPanel = tabId;

        $('#'+tabId).show();
    }
}