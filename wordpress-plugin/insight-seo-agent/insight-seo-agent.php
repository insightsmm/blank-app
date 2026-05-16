<?php
/**
 * Plugin Name: Insight SEO Agent
 * Plugin URI:  https://insightsm.com
 * Description: AI-powered SEO agent — auto-optimises drafts using Claude AI, adds Pexels images, publishes when SEO score ≥ 85.
 * Version:     2.0.0
 * Author:      InsightSMM
 * License:     GPL-2.0+
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

// Constants
define( 'INSIGHT_SEO_VERSION', '2.0.0' );
define( 'INSIGHT_SEO_PATH', plugin_dir_path( __FILE__ ) );
define( 'INSIGHT_SEO_URL', plugin_dir_url( __FILE__ ) );

// Include class files
require_once INSIGHT_SEO_PATH . 'includes/class-seo-scorer.php';
require_once INSIGHT_SEO_PATH . 'includes/class-claude-api.php';
require_once INSIGHT_SEO_PATH . 'includes/class-pexels-api.php';
require_once INSIGHT_SEO_PATH . 'includes/class-agent-runner.php';
require_once INSIGHT_SEO_PATH . 'includes/class-admin-page.php';

// Activation hook
register_activation_hook( __FILE__, 'insight_seo_activate' );
function insight_seo_activate() {
    insight_seo_create_log_table();
    insight_seo_register_cron_intervals();

    if ( ! wp_next_scheduled( 'insight_seo_cron' ) ) {
        $settings = get_option( 'insight_seo_settings', insight_seo_default_settings() );
        wp_schedule_event( time(), $settings['cron_interval'] ?? 'every_five_minutes', 'insight_seo_cron' );
    }
}

// Deactivation hook
register_deactivation_hook( __FILE__, 'insight_seo_deactivate' );
function insight_seo_deactivate() {
    wp_clear_scheduled_hook( 'insight_seo_cron' );
    wp_clear_scheduled_hook( 'insight_seo_process_single' );
}

// Create DB table
function insight_seo_create_log_table() {
    global $wpdb;
    $table_name      = $wpdb->prefix . 'insight_seo_log';
    $charset_collate = $wpdb->get_charset_collate();

    $sql = "CREATE TABLE IF NOT EXISTS {$table_name} (
        id bigint(20) NOT NULL AUTO_INCREMENT,
        post_id bigint(20) NOT NULL DEFAULT 0,
        post_title varchar(255) NOT NULL DEFAULT '',
        post_type varchar(50) NOT NULL DEFAULT 'post',
        seo_score_before int(11) NOT NULL DEFAULT 0,
        seo_score_after int(11) NOT NULL DEFAULT 0,
        status varchar(30) NOT NULL DEFAULT 'processing',
        iterations int(11) NOT NULL DEFAULT 0,
        processed_at datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
        notes text,
        PRIMARY KEY (id),
        KEY post_id (post_id),
        KEY status (status),
        KEY processed_at (processed_at)
    ) {$charset_collate};";

    require_once ABSPATH . 'wp-admin/includes/upgrade.php';
    dbDelta( $sql );
}

// Default settings
function insight_seo_default_settings() {
    return [
        'min_score'      => 85,
        'cron_interval'  => 'every_five_minutes',
        'max_iterations' => 3,
        'include_posts'  => true,
        'include_pages'  => true,
        'auto_publish'   => true,
        'claude_model'   => 'claude-opus-4-7',
    ];
}

// Register cron intervals
function insight_seo_register_cron_intervals() {
    // Intervals are added via filter below
}

add_filter( 'cron_schedules', 'insight_seo_add_cron_intervals' );
function insight_seo_add_cron_intervals( $schedules ) {
    $schedules['every_five_minutes'] = [
        'interval' => 300,
        'display'  => __( 'Every 5 Minutes', 'insight-seo-agent' ),
    ];
    $schedules['every_ten_minutes'] = [
        'interval' => 600,
        'display'  => __( 'Every 10 Minutes', 'insight-seo-agent' ),
    ];
    $schedules['every_thirty_minutes'] = [
        'interval' => 1800,
        'display'  => __( 'Every 30 Minutes', 'insight-seo-agent' ),
    ];
    return $schedules;
}

// Cron handler — process all drafts
add_action( 'insight_seo_cron', 'insight_seo_run_cron' );
function insight_seo_run_cron() {
    $runner = new Insight_SEO_Agent_Runner();
    $runner->process_all_drafts();
}

// Process single post hook
add_action( 'insight_seo_process_single', 'insight_seo_run_single_post' );
function insight_seo_run_single_post( $post_id ) {
    $runner = new Insight_SEO_Agent_Runner();
    $runner->run_on_post( $post_id );
}

// save_post hook — triggers agent on new draft (priority 20)
add_action( 'save_post', 'insight_seo_on_save_post', 20, 3 );
function insight_seo_on_save_post( $post_id, $post, $update ) {
    // Bail on autosave
    if ( defined( 'DOING_AUTOSAVE' ) && DOING_AUTOSAVE ) {
        return;
    }

    // Bail on revisions
    if ( wp_is_post_revision( $post_id ) ) {
        return;
    }

    // Only process drafts of post/page type
    if ( $post->post_status !== 'draft' ) {
        return;
    }

    $allowed_types = [ 'post', 'page' ];
    if ( ! in_array( $post->post_type, $allowed_types, true ) ) {
        return;
    }

    // Only trigger if not already processed
    $already_processed = get_post_meta( $post_id, '_insight_seo_processed', true );
    if ( ! empty( $already_processed ) ) {
        return;
    }

    // Check if already queued
    $queued = get_post_meta( $post_id, '_insight_seo_queued', true );
    if ( ! empty( $queued ) ) {
        return;
    }

    // Mark as queued
    update_post_meta( $post_id, '_insight_seo_queued', current_time( 'mysql' ) );

    // Schedule single event 10 seconds later
    if ( ! wp_next_scheduled( 'insight_seo_process_single', [ $post_id ] ) ) {
        wp_schedule_single_event( time() + 10, 'insight_seo_process_single', [ $post_id ] );
    }
}

// Instantiate admin page and runner
if ( is_admin() ) {
    new Insight_SEO_Admin_Page();
}

// REST API
add_action( 'rest_api_init', 'insight_seo_register_rest_routes' );
function insight_seo_register_rest_routes() {
    // GET /wp-json/insight-seo/v1/logs
    register_rest_route( 'insight-seo/v1', '/logs', [
        'methods'             => 'GET',
        'callback'            => 'insight_seo_rest_get_logs',
        'permission_callback' => 'insight_seo_rest_permission',
    ] );

    // POST /wp-json/insight-seo/v1/run
    register_rest_route( 'insight-seo/v1', '/run', [
        'methods'             => 'POST',
        'callback'            => 'insight_seo_rest_run',
        'permission_callback' => 'insight_seo_rest_permission',
    ] );

    // GET /wp-json/insight-seo/v1/stats
    register_rest_route( 'insight-seo/v1', '/stats', [
        'methods'             => 'GET',
        'callback'            => 'insight_seo_rest_get_stats',
        'permission_callback' => 'insight_seo_rest_permission',
    ] );
}

function insight_seo_rest_permission( WP_REST_Request $request ) {
    // Allow with application passwords or cookie auth
    return current_user_can( 'manage_options' );
}

function insight_seo_rest_get_logs( WP_REST_Request $request ) {
    global $wpdb;
    $table = $wpdb->prefix . 'insight_seo_log';
    // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
    $rows = $wpdb->get_results( $wpdb->prepare(
        "SELECT * FROM `{$table}` ORDER BY processed_at DESC LIMIT %d",
        100
    ) );

    $activity_log = get_option( 'insight_seo_activity_log', '' );
    $lines        = array_slice( array_filter( explode( "\n", $activity_log ) ), -100 );

    return rest_ensure_response( [
        'db_logs'      => $rows,
        'activity_log' => $lines,
    ] );
}

function insight_seo_rest_run( WP_REST_Request $request ) {
    $runner = new Insight_SEO_Agent_Runner();
    $result = $runner->process_all_drafts();
    return rest_ensure_response( $result );
}

function insight_seo_rest_get_stats( WP_REST_Request $request ) {
    global $wpdb;
    $table = $wpdb->prefix . 'insight_seo_log';

    $total_processed = (int) $wpdb->get_var( "SELECT COUNT(*) FROM `{$table}`" ); // phpcs:ignore

    $published_today = (int) $wpdb->get_var( $wpdb->prepare(
        "SELECT COUNT(*) FROM `{$table}` WHERE status = %s AND DATE(processed_at) = %s",
        'published',
        current_time( 'Y-m-d' )
    ) );

    $avg_score = (float) $wpdb->get_var( "SELECT AVG(seo_score_after) FROM `{$table}` WHERE seo_score_after > 0" ); // phpcs:ignore

    $draft_query = new WP_Query( [
        'post_status'    => 'draft',
        'post_type'      => [ 'post', 'page' ],
        'posts_per_page' => -1,
        'fields'         => 'ids',
    ] );
    $draft_count = $draft_query->found_posts;

    return rest_ensure_response( [
        'total_processed' => $total_processed,
        'published_today' => $published_today,
        'avg_score'       => round( $avg_score, 1 ),
        'draft_count'     => $draft_count,
    ] );
}
