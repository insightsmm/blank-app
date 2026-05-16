/**
 * Insight SEO Agent — Admin JavaScript
 *
 * Handles: tab switching, run cycle, process single post,
 * log auto-refresh, test connection, save settings, save API keys.
 */

/* global insightSEO, jQuery */

jQuery(function ($) {
    'use strict';

    var nonce   = insightSEO.nonce;
    var ajaxUrl = insightSEO.ajaxUrl;

    // =========================================================================
    // Tab Switching (pure JS, no page reload)
    // =========================================================================

    function switchTab(tabName) {
        // Update tab links
        $('.insight-seo-tab').each(function () {
            $(this).toggleClass('active', $(this).data('tab') === tabName);
        });

        // Show/hide content
        $('.insight-seo-tab-content').hide();
        $('#tab-' + tabName).show();

        // Auto-load logs when switching to log tab
        if (tabName === 'logs') {
            fetchLogs();
        }

        // Store active tab in sessionStorage
        try {
            sessionStorage.setItem('insightSEOActiveTab', tabName);
        } catch (e) { /* ignore */ }
    }

    // Tab click handler
    $(document).on('click', '.insight-seo-tab', function (e) {
        e.preventDefault();
        switchTab($(this).data('tab'));
    });

    // Restore active tab on page load
    (function () {
        var savedTab = 'dashboard';
        try {
            savedTab = sessionStorage.getItem('insightSEOActiveTab') || 'dashboard';
        } catch (e) { /* ignore */ }
        switchTab(savedTab);
    }());

    // =========================================================================
    // Helper: show inline notice
    // =========================================================================

    function showNotice($el, message, type) {
        $el
            .removeClass('notice-success notice-error notice-warning')
            .addClass('notice-' + (type || 'success'))
            .text(message)
            .show();

        // Auto-hide after 8 seconds
        setTimeout(function () {
            $el.fadeOut(400);
        }, 8000);
    }

    // =========================================================================
    // Run Full Cycle
    // =========================================================================

    var $runBtn     = $('#insight-run-cycle-btn');
    var $runSpinner = $('#insight-run-cycle-spinner');
    var $runResult  = $('#insight-run-cycle-result');

    $runBtn.on('click', function () {
        $runBtn.prop('disabled', true).text('Running...');
        $runSpinner.addClass('is-active');
        $runResult.hide();

        $.post(ajaxUrl, {
            action: 'insight_seo_run_cycle',
            nonce:  nonce
        })
        .done(function (response) {
            if (response.success) {
                showNotice($runResult, '✓ ' + response.data.message, 'success');
                // Reload the page after 1.5 s to refresh stats/tables
                setTimeout(function () {
                    window.location.reload();
                }, 2000);
            } else {
                var msg = response.data && response.data.message ? response.data.message : 'An error occurred.';
                showNotice($runResult, '✗ ' + msg, 'error');
            }
        })
        .fail(function (xhr) {
            showNotice($runResult, '✗ Request failed: ' + (xhr.statusText || 'Unknown error.'), 'error');
        })
        .always(function () {
            $runBtn.prop('disabled', false).text('▶ Run Full Cycle Now');
            $runSpinner.removeClass('is-active');
        });
    });

    // =========================================================================
    // Process Single Post (dashboard table)
    // =========================================================================

    $(document).on('click', '.insight-process-post-btn', function () {
        var $btn     = $(this);
        var $spinner = $btn.siblings('.insight-post-spinner');
        var postId   = $btn.data('post-id');
        var $row     = $btn.closest('tr');

        $btn.prop('disabled', true).text('Processing...');
        $spinner.addClass('is-active');

        $.post(ajaxUrl, {
            action:  'insight_seo_run_post',
            nonce:   nonce,
            post_id: postId
        })
        .done(function (response) {
            if (response.success) {
                var d   = response.data;
                var msg = '✓ ' + d.message;
                $btn.closest('td').html('<span style="color:#065f46; font-size:13px; font-weight:600;">' + msg + '</span>');

                // Update score badge in row if possible
                var afterScore = d.score_after || 0;
                var cls = afterScore >= 75 ? 'score-high' : (afterScore >= 50 ? 'score-mid' : 'score-low');
                $row.find('.score-badge:first').attr('class', 'score-badge ' + cls).text(afterScore);

                // Highlight row
                $row.css('background', '#d1fae5');
                setTimeout(function () {
                    $row.css('background', '');
                }, 3000);
            } else {
                var errMsg = response.data && response.data.message ? response.data.message : 'Failed.';
                $btn.text('Retry').prop('disabled', false);
                $spinner.removeClass('is-active');
                $btn.closest('td').append('<br><span style="color:#991b1b; font-size:12px;">' + errMsg + '</span>');
            }
        })
        .fail(function (xhr) {
            $btn.text('Retry').prop('disabled', false);
            $spinner.removeClass('is-active');
            $btn.closest('td').append('<br><span style="color:#991b1b; font-size:12px;">Request failed.</span>');
        })
        .always(function () {
            $spinner.removeClass('is-active');
        });
    });

    // =========================================================================
    // Save Settings
    // =========================================================================

    var $settingsForm    = $('#insight-settings-form');
    var $settingsNotice  = $('#insight-settings-notice');
    var $settingsSpinner = $('#insight-settings-spinner');

    $settingsForm.on('submit', function (e) {
        e.preventDefault();

        var $btn = $('#insight-save-settings-btn');
        $btn.prop('disabled', true);
        $settingsSpinner.addClass('is-active');
        $settingsNotice.hide();

        var data = {
            action: 'insight_seo_save_settings',
            nonce:  nonce
        };

        // Serialize checkboxes properly
        $settingsForm.find('input[type="checkbox"]').each(function () {
            data[this.name] = this.checked ? '1' : '0';
        });

        // Serialize other fields
        $settingsForm.find('input[type="number"], select').each(function () {
            data[this.name] = $(this).val();
        });

        $.post(ajaxUrl, data)
        .done(function (response) {
            if (response.success) {
                showNotice($settingsNotice, '✓ ' + response.data.message, 'success');
            } else {
                var msg = response.data && response.data.message ? response.data.message : 'Save failed.';
                showNotice($settingsNotice, '✗ ' + msg, 'error');
            }
        })
        .fail(function () {
            showNotice($settingsNotice, '✗ Request failed.', 'error');
        })
        .always(function () {
            $btn.prop('disabled', false);
            $settingsSpinner.removeClass('is-active');
        });
    });

    // =========================================================================
    // Save API Keys
    // =========================================================================

    var $apiKeysForm    = $('#insight-apikeys-form');
    var $apiKeysNotice  = $('#insight-apikeys-notice');
    var $apiKeysSpinner = $('#insight-apikeys-spinner');

    $apiKeysForm.on('submit', function (e) {
        e.preventDefault();

        var $btn = $('#insight-save-apikeys-btn');
        $btn.prop('disabled', true);
        $apiKeysSpinner.addClass('is-active');
        $apiKeysNotice.hide();

        $.post(ajaxUrl, {
            action:      'insight_seo_save_api_keys',
            nonce:       nonce,
            claude_key:  $('#claude_key').val(),
            pexels_key:  $('#pexels_key').val()
        })
        .done(function (response) {
            if (response.success) {
                showNotice($apiKeysNotice, '✓ ' + response.data.message, 'success');
                // Clear password fields after save
                $('#claude_key, #pexels_key').val('');
            } else {
                var msg = response.data && response.data.message ? response.data.message : 'Save failed.';
                showNotice($apiKeysNotice, '✗ ' + msg, 'error');
            }
        })
        .fail(function () {
            showNotice($apiKeysNotice, '✗ Request failed.', 'error');
        })
        .always(function () {
            $btn.prop('disabled', false);
            $apiKeysSpinner.removeClass('is-active');
        });
    });

    // =========================================================================
    // Test Connection
    // =========================================================================

    var $testBtn     = $('#insight-test-connection-btn');
    var $testSpinner = $('#insight-test-spinner');
    var $testResult  = $('#insight-test-result');

    $testBtn.on('click', function () {
        $testBtn.prop('disabled', true).text('Testing...');
        $testSpinner.addClass('is-active');
        $testResult.hide().empty();

        $.post(ajaxUrl, {
            action: 'insight_seo_test_connection',
            nonce:  nonce
        })
        .done(function (response) {
            if (response.success) {
                var d       = response.data;
                var results = d.results || {};
                var html    = '';

                $.each(results, function (service, result) {
                    var icon    = result.success ? '✓' : '✗';
                    var cls     = result.success ? 'test-ok' : 'test-fail';
                    var label   = service.charAt(0).toUpperCase() + service.slice(1);
                    html += '<div class="test-item">';
                    html += '<span class="test-label">' + label + '</span>';
                    html += '<span class="' + cls + '">' + icon + ' ' + (result.message || '') + '</span>';
                    html += '</div>';
                });

                $testResult.html(html).show();
            } else {
                var msg = response.data && response.data.message ? response.data.message : 'Test failed.';
                $testResult
                    .html('<span style="color:#991b1b;">✗ ' + msg + '</span>')
                    .show();
            }
        })
        .fail(function () {
            $testResult
                .html('<span style="color:#991b1b;">✗ Request failed.</span>')
                .show();
        })
        .always(function () {
            $testBtn.prop('disabled', false).text('Test Connection');
            $testSpinner.removeClass('is-active');
        });
    });

    // =========================================================================
    // Logs — fetch and auto-refresh
    // =========================================================================

    var $logViewer   = $('#insight-seo-log-viewer');
    var $logsSpinner = $('#insight-logs-spinner');
    var logInterval  = null;

    function fetchLogs() {
        $logsSpinner.addClass('is-active');

        $.post(ajaxUrl, {
            action: 'insight_seo_get_logs',
            nonce:  nonce
        })
        .done(function (response) {
            if (response.success) {
                var log = response.data.log || '(No activity logged yet.)';
                $logViewer.text(log);
                // Auto-scroll to bottom
                $logViewer.scrollTop($logViewer[0].scrollHeight);
            }
        })
        .always(function () {
            $logsSpinner.removeClass('is-active');
        });
    }

    // Refresh button
    $('#insight-refresh-logs-btn').on('click', fetchLogs);

    // Clear logs button
    $('#insight-clear-logs-btn').on('click', function () {
        if (!window.confirm('Clear all activity logs? This cannot be undone.')) {
            return;
        }

        $logsSpinner.addClass('is-active');

        $.post(ajaxUrl, {
            action: 'insight_seo_clear_logs',
            nonce:  nonce
        })
        .done(function (response) {
            if (response.success) {
                $logViewer.text(response.data.log || '(Logs cleared.)');
            }
        })
        .always(function () {
            $logsSpinner.removeClass('is-active');
        });
    });

    // Auto-refresh logs every 30 seconds when logs tab is active
    function startLogAutoRefresh() {
        if (logInterval) {
            clearInterval(logInterval);
        }
        logInterval = setInterval(function () {
            // Only refresh if logs tab is visible
            if ($('#tab-logs').is(':visible')) {
                fetchLogs();
            }
        }, 30000);
    }

    startLogAutoRefresh();

    // Stop auto-refresh when page is hidden (battery/performance saving)
    document.addEventListener('visibilitychange', function () {
        if (document.hidden) {
            if (logInterval) {
                clearInterval(logInterval);
                logInterval = null;
            }
        } else {
            startLogAutoRefresh();
            // Refresh immediately on focus
            if ($('#tab-logs').is(':visible')) {
                fetchLogs();
            }
        }
    });

});
