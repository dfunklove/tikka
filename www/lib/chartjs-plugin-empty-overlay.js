/*
The MIT License (MIT)

Copyright (c) 2017 NeverBounce

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Note: This program was changed from its original form by Daniel Lovette.
*/

'use strict';

var CHART_EMPTY_MSG_TIMEOUT = 60000; // 1 minute

(function() {

    var Chart = window.Chart;
    var helpers = Chart.helpers;

    Chart.defaults.global.emptyOverlay = {
        enabled: true,
        message: 'No data available',
        fillStyle: 'rgba(100,100,100,0.3)',
        fontColor: 'rgba(100,100,100,1.0)',
        fontStroke: 'rgba(255,255,255,0.6)',
        fontStrokeWidth: '3',
        fontSize: 'auto',
    };

    /**
     * Checks if the chart is currently empty
     * @param datasets
     * @param model
     * @returns {boolean}
     */
    function isChartEmpty(datasets, model) {
        return (model.isEmpty = values.length < 2);
    }

    function updateMessage(model) {
        var message;
        if (!subscription) {
            message = "Enter a symbol..."
        } else if (Date.now() - subscribeTime < CHART_EMPTY_MSG_TIMEOUT) {
            message = "Waiting for data..."
        } else {
            message = "No data available"
        }
        return (model.options.message = message);
    }

    Chart.EmptyOverlay = Chart.Element.extend({

        position: 'chartArea',

        initialize: function(config) {
            helpers.extend(this, config);
        },

        // Shared Methods
        isHorizontal: function() {
            return this.options.position === 'top' ||
                this.options.position === 'bottom';
        },

        // no-op
        update: function() {
        },

        // Actually draw the legend on the canvas
        draw: function() {
            var me = this;
            var ctx = me.ctx;

            var globalDefault = Chart.defaults.global;
            var emptyOpts = me.options;
            var chartArea = me.chart.chartArea,
                x = chartArea.left,
                y = chartArea.top,
                width = chartArea.right - chartArea.left,
                height = chartArea.bottom - chartArea.top,
                textX = (x / 2) + (width / 2),
                textY = y + (height / 2),
                itemOrDefault = helpers.getValueOrDefault,
                message = emptyOpts.message,
                fontSizeOpt = itemOrDefault(emptyOpts.fontSize,
                    globalDefault.defaultFontSize),
                fontSize = (fontSizeOpt === 'auto' ?
                    (Math.sqrt(width)) :
                    fontSizeOpt),
                fontStyle = itemOrDefault(emptyOpts.fontStyle,
                    globalDefault.defaultFontStyle),
                fontFamily = itemOrDefault(emptyOpts.fontFamily,
                    globalDefault.defaultFontFamily),
                labelFont = helpers.fontString(fontSize, fontStyle, fontFamily);

            ctx.fillStyle = itemOrDefault(emptyOpts.fillStyle,
                globalDefault.defaultColor);
            ctx.fillRect(x, y, width, height);

            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.font = labelFont;
            ctx.lineWidth = emptyOpts.fontStrokeWidth;
            ctx.miterLimit = 2;
            ctx.strokeStyle = emptyOpts.fontStroke;
            ctx.strokeText(message, textX, textY, width);

            ctx.fillStyle = itemOrDefault(emptyOpts.fontColor,
                globalDefault.defaultFontColor);
            ctx.fillText(message, textX, textY, width);
        },
    });

    function createNewEmptyOverlay(chartInstance, emptyOpts) {
        var emptyOverlay = new Chart.EmptyOverlay({
            ctx: chartInstance.chart.ctx,
            options: emptyOpts,
            originalConfig: chartInstance.config,
            chart: chartInstance,
            isEmpty: false,
        });
        chartInstance.emptyOverlay = emptyOverlay;
    }

    // Register the emptyOverlay plugin
    Chart.plugins.register({
        beforeInit: function(chartInstance) {

            // Merge config
            var emptyOpts = chartInstance.options.emptyOverlay || {};
            emptyOpts = helpers.configMerge(Chart.defaults.global.emptyOverlay,
                emptyOpts);

            // Add config and create object
            createNewEmptyOverlay(chartInstance, emptyOpts);
        },

        afterDatasetsDraw: function(chartInstance) {

            // Merge config
            var emptyOpts = chartInstance.options.emptyOverlay || {};
            emptyOpts = helpers.configMerge(Chart.defaults.global.emptyOverlay,
                emptyOpts);

            // Add config and create object if needed
            if (!chartInstance.emptyOverlay)
                createNewEmptyOverlay(chartInstance, emptyOpts);
            else
                chartInstance.emptyOverlay.options = emptyOpts;
            
            // Populate isEmpty on the chartInstance
            isChartEmpty(chartInstance.config.data.datasets,
                    chartInstance.emptyOverlay);

            // Check if this is enabled and chart is empty
            if (emptyOpts.enabled && chartInstance.emptyOverlay.isEmpty) {

                updateMessage(chartInstance.emptyOverlay);

                // Check if it's already rendered
                if (!chartInstance.emptyOverlayBox) {
                    chartInstance.emptyOverlayBox = true;
                    Chart.layoutService.addBox(chartInstance,
                        chartInstance.emptyOverlay);
                }
            } else if (chartInstance.emptyOverlayBox) {
                Chart.layoutService.removeBox(chartInstance,
                    chartInstance.emptyOverlay);
                delete chartInstance.emptyOverlayBox;
            }
        },
    });
}());