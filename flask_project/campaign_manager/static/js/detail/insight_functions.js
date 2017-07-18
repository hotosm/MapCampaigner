function renderInsightFunctions(username) {

    $.each(selected_functions, function (key, selected_function) {

        var insightPanel = $('.advance-insights').clone()[0];
        var $insightPanel = $(insightPanel);
        $('#page-wrapper').append($insightPanel);
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
                var tab_name = selected_function['name'];
                $insightTitle.html(tab_name);
                $insightContent.append(
                    '<div id="' + tab_id + '">' +
                        '<span class="grey-italic" style="margin-top:15px !important; position: absolute;"> Loading data .. </span>' +
                    '</div>'
                );
                getInsightFunctions(key);
                if (!containsObject(selected_function['feature'], feature_collected)) {
                    feature_collected.push(selected_function['feature']);
                }
            }
        }
    });

    for (var i = 0; i < feature_collected.length; i++) {
        calculateContributors(feature_collected[i]);
    }

    renderRemoteProjects();
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
        progress = remaining_days / campaign_range * 100;
    }

    $('#campaign-progress').css({
        'width': progress + '%'
    })
}

function getInsightFunctions(function_id) {
    var url = '/campaign_manager/campaign/' + uuid + '/' + function_id;
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
        }

        $insightTabs.find('a[href="#' + tabId + '"]').closest('li').remove();
        $insightTabs.append(
                '<li class="' + active + '">' +
                '<a href="#' + tabId + '" data-toggle="tab" aria-expanded="true">' +
                    tabName + '</a>' +
                '</li>'
        );

        $insightContent.find('#' + key).remove();
        $insightContent.append(
            '<div class="tab-pane fade ' + active + ' in" id="' + tabId + '"></div>'
        );

        var $typeContents = $('#'+tabId);

        $typeContents.append('<div class="row insight-type-content"></div>');
        $typeContents.append('<div class="row insight-type-sub-content"></div>');

        var $mainRowTypeContents = $('#'+tabId+ ' .insight-type-content');

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
                    $mainRowTypeContents.append(
                            '<div class="col-lg-6" id="' + insightId + '">' +
                            '<span class="grey-italic" style="margin-top:15px !important; position: absolute;"> ' +
                                'Loading data .. </span>' +
                            '</div>'
                    );

                    getInsightFunctions(insightId);
                    if (!containsObject(selected_function['feature'], feature_collected)) {
                        feature_collected.push(selected_function['feature']);
                    }
                }
            }
        });

        index++;
    }

    renderInsightFunctions(username);
}

