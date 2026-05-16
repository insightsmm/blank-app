<?php
/**
 * Admin Page — renders the Insight SEO Agent dashboard in WP admin.
 *
 * @package Insight_SEO_Agent
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

class Insight_SEO_Admin_Page {

    /** @var string */
    private $page_slug = 'insight-chatgpt-agents-app';

    /**
     * Constructor — hooks everything.
     */
    public function __construct() {
        add_action( 'admin_menu',            [ $this, 'register_menu' ] );
        add_action( 'admin_enqueue_scripts', [ $this, 'enqueue_assets' ] );

        // AJAX handlers
        add_action( 'wp_ajax_insight_seo_run_cycle',       [ $this, 'ajax_run_cycle' ] );
        add_action( 'wp_ajax_insight_seo_run_post',        [ $this, 'ajax_run_post' ] );
        add_action( 'wp_ajax_insight_seo_get_logs',        [ $this, 'ajax_get_logs' ] );
        add_action( 'wp_ajax_insight_seo_test_connection', [ $this, 'ajax_test_connection' ] );
        add_action( 'wp_ajax_insight_seo_save_settings',  [ $this, 'ajax_save_settings' ] );
        add_action( 'wp_ajax_insight_seo_save_api_keys',  [ $this, 'ajax_save_api_keys' ] );
        add_action( 'wp_ajax_insight_seo_clear_logs',     [ $this, 'ajax_clear_logs' ] );
    }

    /**
     * Register admin menu page.
     */
    public function register_menu() {
        add_menu_page(
            'Insight SEO Agent',
            'SEO Agent',
            'manage_options',
            $this->page_slug,
            [ $this, 'render_page' ],
            'dashicons-chart-line',
            30
        );
    }

    /**
     * Enqueue CSS and JS assets.
     *
     * @param string $hook Current admin page hook.
     */
    public function enqueue_assets( $hook ) {
        if ( strpos( $hook, $this->page_slug ) === false ) {
            return;
        }

        wp_enqueue_style(
            'insight-seo-admin',
            INSIGHT_SEO_URL . 'assets/admin.css',
            [],
            INSIGHT_SEO_VERSION
        );

        wp_enqueue_script(
            'insight-seo-admin',
            INSIGHT_SEO_URL . 'assets/admin.js',
            [ 'jquery' ],
            INSIGHT_SEO_VERSION,
            true
        );

        wp_localize_script( 'insight-seo-admin', 'insightSEO', [
            'ajaxUrl'   => admin_url( 'admin-ajax.php' ),
            'nonce'     => wp_create_nonce( 'insight_seo_nonce' ),
            'adminUrl'  => admin_url(),
        ] );
    }

    /**
     * Render the full admin page.
     */
    public function render_page() {
        if ( ! current_user_can( 'manage_options' ) ) {
            wp_die( esc_html__( 'You do not have permission to access this page.', 'insight-seo-agent' ) );
        }

        $settings    = $this->get_settings();
        $api_keys    = get_option( 'insight_seo_api_keys', [] );
        $agent_active = (bool) wp_next_scheduled( 'insight_seo_cron' );

        // Stat counts
        $draft_count     = $this->get_draft_count();
        $published_today = $this->get_published_today();
        $avg_score       = $this->get_avg_score();

        ?>
        <div class="wrap insight-seo-wrap">
            <div class="insight-seo-header">
                <div class="insight-seo-logo">Insight <span>SEO</span> Agent</div>
                <span class="insight-seo-badge <?php echo $agent_active ? 'badge-active' : 'badge-paused'; ?>">
                    <?php echo $agent_active ? '&#9679; Agent Active' : '&#9675; Agent Paused'; ?>
                </span>
                <button id="insight-run-cycle-btn" class="button insight-seo-run-btn">
                    &#9654; Run Full Cycle Now
                </button>
                <span id="insight-run-cycle-spinner" class="spinner" style="float:none; margin:0;"></span>
            </div>

            <div id="insight-run-cycle-result" style="display:none;" class="notice" role="alert"></div>

            <!-- Stats Row -->
            <div class="insight-seo-stats">
                <div class="stat-box">
                    <div class="stat-number"><?php echo esc_html( $draft_count ); ?></div>
                    <div class="stat-label">Draft Posts</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number"><?php echo esc_html( $published_today ); ?></div>
                    <div class="stat-label">Published Today</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number"><?php echo esc_html( $avg_score > 0 ? $avg_score : '--' ); ?></div>
                    <div class="stat-label">Avg SEO Score</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">
                        <span style="font-size:22px; color:<?php echo $agent_active ? '#10b981' : '#ef4444'; ?>;">
                            <?php echo $agent_active ? 'ON' : 'OFF'; ?>
                        </span>
                    </div>
                    <div class="stat-label">Agent Status</div>
                </div>
            </div>

            <!-- Tabs -->
            <div class="insight-seo-tabs" role="tablist">
                <a class="insight-seo-tab active" href="#" data-tab="dashboard" role="tab">&#9783; Dashboard</a>
                <a class="insight-seo-tab" href="#" data-tab="settings" role="tab">&#9881; Agent Settings</a>
                <a class="insight-seo-tab" href="#" data-tab="apikeys" role="tab">&#128273; API Keys</a>
                <a class="insight-seo-tab" href="#" data-tab="logs" role="tab">&#128196; Activity Logs</a>
            </div>

            <!-- Dashboard Tab -->
            <div id="tab-dashboard" class="insight-seo-tab-content">
                <h2>Recent Processing Log</h2>
                <?php $this->render_log_table(); ?>

                <h2 style="margin-top: 32px;">Current Drafts</h2>
                <?php $this->render_drafts_table(); ?>
            </div>

            <!-- Settings Tab -->
            <div id="tab-settings" class="insight-seo-tab-content" style="display:none;">
                <h2>Agent Settings</h2>
                <div id="insight-settings-notice" class="notice" style="display:none;" role="alert"></div>
                <form id="insight-settings-form">
                    <table class="form-table" role="presentation">
                        <tbody>
                            <tr>
                                <th scope="row"><label for="min_score">Min SEO Score to Publish</label></th>
                                <td>
                                    <input type="number" id="min_score" name="min_score"
                                        value="<?php echo esc_attr( $settings['min_score'] ); ?>"
                                        min="1" max="100" class="small-text" />
                                    <p class="description">Posts will be auto-published when score reaches this threshold (default: 85).</p>
                                </td>
                            </tr>
                            <tr>
                                <th scope="row"><label for="cron_interval">Cron Interval</label></th>
                                <td>
                                    <select id="cron_interval" name="cron_interval">
                                        <option value="every_five_minutes" <?php selected( $settings['cron_interval'], 'every_five_minutes' ); ?>>Every 5 Minutes</option>
                                        <option value="every_ten_minutes" <?php selected( $settings['cron_interval'], 'every_ten_minutes' ); ?>>Every 10 Minutes</option>
                                        <option value="every_thirty_minutes" <?php selected( $settings['cron_interval'], 'every_thirty_minutes' ); ?>>Every 30 Minutes</option>
                                        <option value="hourly" <?php selected( $settings['cron_interval'], 'hourly' ); ?>>Hourly</option>
                                    </select>
                                </td>
                            </tr>
                            <tr>
                                <th scope="row"><label for="max_iterations">Max Iterations per Post</label></th>
                                <td>
                                    <input type="number" id="max_iterations" name="max_iterations"
                                        value="<?php echo esc_attr( $settings['max_iterations'] ); ?>"
                                        min="1" max="10" class="small-text" />
                                    <p class="description">Maximum number of Claude optimization passes per post (default: 3).</p>
                                </td>
                            </tr>
                            <tr>
                                <th scope="row">Post Types</th>
                                <td>
                                    <label>
                                        <input type="checkbox" name="include_posts" value="1"
                                            <?php checked( ! empty( $settings['include_posts'] ) ); ?> />
                                        Include Posts
                                    </label>
                                    <br />
                                    <label>
                                        <input type="checkbox" name="include_pages" value="1"
                                            <?php checked( ! empty( $settings['include_pages'] ) ); ?> />
                                        Include Pages
                                    </label>
                                </td>
                            </tr>
                            <tr>
                                <th scope="row">Auto-Publish</th>
                                <td>
                                    <label>
                                        <input type="checkbox" name="auto_publish" value="1"
                                            <?php checked( ! empty( $settings['auto_publish'] ) ); ?> />
                                        Automatically publish posts when SEO score threshold is reached
                                    </label>
                                </td>
                            </tr>
                            <tr>
                                <th scope="row"><label for="claude_model">Claude Model</label></th>
                                <td>
                                    <select id="claude_model" name="claude_model">
                                        <option value="claude-opus-4-7" <?php selected( $settings['claude_model'], 'claude-opus-4-7' ); ?>>Claude Opus 4.7 (Most Capable)</option>
                                        <option value="claude-sonnet-4-6" <?php selected( $settings['claude_model'], 'claude-sonnet-4-6' ); ?>>Claude Sonnet 4.6 (Balanced)</option>
                                        <option value="claude-haiku-4-5-20251001" <?php selected( $settings['claude_model'], 'claude-haiku-4-5-20251001' ); ?>>Claude Haiku 4.5 (Fast)</option>
                                    </select>
                                    <p class="description">Choose the Claude model for SEO optimization. Opus is most capable but slower.</p>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <p class="submit">
                        <button type="submit" id="insight-save-settings-btn" class="button button-primary">Save Settings</button>
                        <span id="insight-settings-spinner" class="spinner" style="float:none; margin:0 8px;"></span>
                    </p>
                </form>
            </div>

            <!-- API Keys Tab -->
            <div id="tab-apikeys" class="insight-seo-tab-content" style="display:none;">
                <h2>API Keys</h2>
                <div id="insight-apikeys-notice" class="notice" style="display:none;" role="alert"></div>

                <?php if ( empty( $api_keys['claude_key'] ) ) : ?>
                    <div class="notice notice-warning inline">
                        <p><strong>Claude API key not set.</strong> The SEO agent will not run until a valid Claude API key is configured.</p>
                    </div>
                <?php endif; ?>

                <form id="insight-apikeys-form">
                    <table class="form-table" role="presentation">
                        <tbody>
                            <tr>
                                <th scope="row"><label for="claude_key">Claude API Key</label></th>
                                <td>
                                    <input type="password" id="claude_key" name="claude_key"
                                        placeholder="<?php echo ! empty( $api_keys['claude_key'] ) ? '****' . substr( $api_keys['claude_key'], -4 ) : 'sk-ant-...'; ?>"
                                        class="regular-text" autocomplete="new-password" />
                                    <?php if ( ! empty( $api_keys['claude_key'] ) ) : ?>
                                        <span style="color:#10b981; margin-left:8px;">&#10003; Key set (ends in <?php echo esc_html( substr( $api_keys['claude_key'], -4 ) ); ?>)</span>
                                    <?php endif; ?>
                                    <p class="description">Get your API key at <a href="https://console.anthropic.com" target="_blank">console.anthropic.com</a>. Leave blank to keep existing key.</p>
                                </td>
                            </tr>
                            <tr>
                                <th scope="row"><label for="pexels_key">Pexels API Key</label></th>
                                <td>
                                    <input type="password" id="pexels_key" name="pexels_key"
                                        placeholder="<?php echo ! empty( $api_keys['pexels_key'] ) ? '****' . substr( $api_keys['pexels_key'], -4 ) : 'Enter Pexels API key...'; ?>"
                                        class="regular-text" autocomplete="new-password" />
                                    <?php if ( ! empty( $api_keys['pexels_key'] ) ) : ?>
                                        <span style="color:#10b981; margin-left:8px;">&#10003; Key set (ends in <?php echo esc_html( substr( $api_keys['pexels_key'], -4 ) ); ?>)</span>
                                    <?php endif; ?>
                                    <p class="description">Get your API key at <a href="https://www.pexels.com/api/" target="_blank">pexels.com/api</a>. Leave blank to keep existing key. Images will be skipped if not set.</p>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <p class="submit">
                        <button type="submit" id="insight-save-apikeys-btn" class="button button-primary">Save API Keys</button>
                        <span id="insight-apikeys-spinner" class="spinner" style="float:none; margin:0 8px;"></span>
                        <button type="button" id="insight-test-connection-btn" class="button button-secondary" style="margin-left:16px;">
                            Test Connection
                        </button>
                        <span id="insight-test-spinner" class="spinner" style="float:none; margin:0 8px;"></span>
                    </p>
                </form>

                <div id="insight-test-result" style="margin-top:16px; display:none;"></div>
            </div>

            <!-- Logs Tab -->
            <div id="tab-logs" class="insight-seo-tab-content" style="display:none;">
                <h2>Activity Log
                    <button type="button" id="insight-refresh-logs-btn" class="button button-secondary" style="margin-left:16px; font-size:13px;">
                        &#8635; Refresh
                    </button>
                    <button type="button" id="insight-clear-logs-btn" class="button" style="margin-left:8px; font-size:13px; color:#991b1b;">
                        &#128465; Clear Logs
                    </button>
                    <span id="insight-logs-spinner" class="spinner" style="float:none; margin:0 8px;"></span>
                </h2>
                <p style="color:#6b7280; font-size:13px;">Auto-refreshes every 30 seconds. Showing last 200 lines.</p>
                <div id="insight-seo-log-viewer" role="log" aria-live="polite"><?php
                    $log = get_option( 'insight_seo_activity_log', '' );
                    echo esc_html( $log ?: '(No activity logged yet.)' );
                ?></div>
            </div>

        </div><!-- .insight-seo-wrap -->
        <?php
    }

    /**
     * Render the recent log entries table.
     */
    private function render_log_table() {
        global $wpdb;
        $table = $wpdb->prefix . 'insight_seo_log';
        // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
        $logs = $wpdb->get_results( $wpdb->prepare( "SELECT * FROM `{$table}` ORDER BY processed_at DESC LIMIT %d", 20 ) );

        if ( empty( $logs ) ) {
            echo '<p style="color:#6b7280;">No posts have been processed yet. Run the agent or wait for the next cron cycle.</p>';
            return;
        }

        echo '<table class="wp-list-table widefat fixed striped">';
        echo '<thead><tr>
            <th>Post Title</th>
            <th style="width:60px">Type</th>
            <th style="width:80px">Before</th>
            <th style="width:80px">After</th>
            <th style="width:100px">Status</th>
            <th style="width:60px">Iters</th>
            <th style="width:130px">Date</th>
        </tr></thead><tbody>';

        foreach ( $logs as $log ) {
            $post_url = get_edit_post_link( $log->post_id );
            $title    = ! empty( $log->post_title ) ? $log->post_title : '(untitled)';

            $before_class = $this->score_class( $log->seo_score_before );
            $after_class  = $this->score_class( $log->seo_score_after );
            $status_class = 'status-' . esc_attr( $log->status );

            echo '<tr>';
            echo '<td>' . ( $post_url ? '<a href="' . esc_url( $post_url ) . '">' . esc_html( $title ) . '</a>' : esc_html( $title ) ) . '</td>';
            echo '<td>' . esc_html( $log->post_type ) . '</td>';
            echo '<td><span class="score-badge ' . esc_attr( $before_class ) . '">' . esc_html( $log->seo_score_before ) . '</span></td>';
            echo '<td><span class="score-badge ' . esc_attr( $after_class ) . '">' . esc_html( $log->seo_score_after ) . '</span></td>';
            echo '<td><span class="score-badge ' . esc_attr( $status_class ) . '">' . esc_html( ucfirst( $log->status ) ) . '</span></td>';
            echo '<td>' . esc_html( $log->iterations ) . '</td>';
            echo '<td>' . esc_html( $log->processed_at ) . '</td>';
            echo '</tr>';
        }

        echo '</tbody></table>';
    }

    /**
     * Render the current drafts table with "Process Now" buttons.
     */
    private function render_drafts_table() {
        $drafts = get_posts( [
            'post_status'    => 'draft',
            'post_type'      => [ 'post', 'page' ],
            'posts_per_page' => 20,
            'orderby'        => 'date',
            'order'          => 'DESC',
        ] );

        if ( empty( $drafts ) ) {
            echo '<p style="color:#6b7280;">No draft posts found.</p>';
            return;
        }

        $scorer = new Insight_SEO_Scorer();

        echo '<table class="wp-list-table widefat fixed striped">';
        echo '<thead><tr>
            <th>Title</th>
            <th style="width:60px">Type</th>
            <th style="width:80px">Current Score</th>
            <th style="width:80px">Words</th>
            <th style="width:110px">Created</th>
            <th style="width:130px">Action</th>
        </tr></thead><tbody>';

        foreach ( $drafts as $post ) {
            $score_data = $scorer->calculate( $post->ID );
            $score      = $score_data['total'];
            $score_cls  = $this->score_class( $score );
            $edit_url   = get_edit_post_link( $post->ID );

            echo '<tr>';
            echo '<td>' . ( $edit_url ? '<a href="' . esc_url( $edit_url ) . '">' . esc_html( $post->post_title ?: '(untitled)' ) . '</a>' : esc_html( $post->post_title ?: '(untitled)' ) ) . '</td>';
            echo '<td>' . esc_html( $post->post_type ) . '</td>';
            echo '<td><span class="score-badge ' . esc_attr( $score_cls ) . '">' . esc_html( $score ) . '</span></td>';
            echo '<td>' . esc_html( $score_data['word_count'] ) . '</td>';
            echo '<td>' . esc_html( $post->post_date ) . '</td>';
            echo '<td>
                <button class="button button-small insight-process-post-btn" data-post-id="' . esc_attr( $post->ID ) . '">
                    Process Now
                </button>
                <span class="spinner insight-post-spinner" style="float:none; margin:0;"></span>
            </td>';
            echo '</tr>';
        }

        echo '</tbody></table>';
    }

    /**
     * Return CSS class for a score badge.
     *
     * @param int $score
     * @return string
     */
    private function score_class( $score ) {
        if ( $score >= 75 ) {
            return 'score-high';
        }
        if ( $score >= 50 ) {
            return 'score-mid';
        }
        return 'score-low';
    }

    /**
     * Get current settings with defaults.
     *
     * @return array
     */
    private function get_settings() {
        $defaults = function_exists( 'insight_seo_default_settings' )
            ? insight_seo_default_settings()
            : [
                'min_score'      => 85,
                'cron_interval'  => 'every_five_minutes',
                'max_iterations' => 3,
                'include_posts'  => true,
                'include_pages'  => true,
                'auto_publish'   => true,
                'claude_model'   => 'claude-opus-4-7',
            ];
        return wp_parse_args( get_option( 'insight_seo_settings', [] ), $defaults );
    }

    /**
     * Count current draft posts/pages.
     *
     * @return int
     */
    private function get_draft_count() {
        $query = new WP_Query( [
            'post_status'    => 'draft',
            'post_type'      => [ 'post', 'page' ],
            'posts_per_page' => -1,
            'fields'         => 'ids',
        ] );
        return (int) $query->found_posts;
    }

    /**
     * Count posts published today via the agent.
     *
     * @return int
     */
    private function get_published_today() {
        global $wpdb;
        $table = $wpdb->prefix . 'insight_seo_log';
        return (int) $wpdb->get_var(
            $wpdb->prepare(
                "SELECT COUNT(*) FROM `{$table}` WHERE status = %s AND DATE(processed_at) = %s",
                'published',
                current_time( 'Y-m-d' )
            )
        );
    }

    /**
     * Get average SEO score after processing.
     *
     * @return string
     */
    private function get_avg_score() {
        global $wpdb;
        $table = $wpdb->prefix . 'insight_seo_log';
        // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
        $avg = $wpdb->get_var( "SELECT AVG(seo_score_after) FROM `{$table}` WHERE seo_score_after > 0" );
        return $avg ? round( (float) $avg, 1 ) : 0;
    }

    // -------------------------------------------------------------------------
    // AJAX Handlers
    // -------------------------------------------------------------------------

    /**
     * AJAX: Run full agent cycle.
     */
    public function ajax_run_cycle() {
        check_ajax_referer( 'insight_seo_nonce', 'nonce' );

        if ( ! current_user_can( 'manage_options' ) ) {
            wp_send_json_error( [ 'message' => 'Permission denied.' ], 403 );
        }

        $runner = new Insight_SEO_Agent_Runner();
        $result = $runner->process_all_drafts();

        wp_send_json_success( [
            'message'   => sprintf(
                'Cycle complete. Processed: %d, Published: %d, Failed: %d, Skipped: %d.',
                $result['processed'],
                $result['published'],
                $result['failed'],
                $result['skipped']
            ),
            'processed' => $result['processed'],
            'published' => $result['published'],
            'failed'    => $result['failed'],
            'skipped'   => $result['skipped'],
        ] );
    }

    /**
     * AJAX: Process a single post.
     */
    public function ajax_run_post() {
        check_ajax_referer( 'insight_seo_nonce', 'nonce' );

        if ( ! current_user_can( 'manage_options' ) ) {
            wp_send_json_error( [ 'message' => 'Permission denied.' ], 403 );
        }

        $post_id = isset( $_POST['post_id'] ) ? (int) $_POST['post_id'] : 0;

        if ( ! $post_id ) {
            wp_send_json_error( [ 'message' => 'Invalid post ID.' ] );
        }

        // Remove the processed flag so the agent re-runs
        delete_post_meta( $post_id, '_insight_seo_processed' );
        delete_post_meta( $post_id, '_insight_seo_queued' );

        $runner = new Insight_SEO_Agent_Runner();
        $result = $runner->run_on_post( $post_id );

        if ( isset( $result['status'] ) && $result['status'] === 'failed' ) {
            wp_send_json_error( [
                'message'      => 'Processing failed: ' . ( $result['error'] ?? 'Unknown error.' ),
                'score_before' => $result['score_before'] ?? 0,
                'score_after'  => $result['score_after'] ?? 0,
            ] );
        }

        wp_send_json_success( [
            'message'      => sprintf(
                'Post "%s" optimized. Score: %d → %d (%s).',
                $result['post_title'] ?? '',
                $result['score_before'] ?? 0,
                $result['score_after'] ?? 0,
                ucfirst( $result['status'] ?? '' )
            ),
            'status'       => $result['status'],
            'score_before' => $result['score_before'] ?? 0,
            'score_after'  => $result['score_after'] ?? 0,
            'iterations'   => $result['iterations'] ?? 0,
        ] );
    }

    /**
     * AJAX: Get activity log.
     */
    public function ajax_get_logs() {
        check_ajax_referer( 'insight_seo_nonce', 'nonce' );

        if ( ! current_user_can( 'manage_options' ) ) {
            wp_send_json_error( [ 'message' => 'Permission denied.' ], 403 );
        }

        $log   = get_option( 'insight_seo_activity_log', '' );
        $lines = array_filter( explode( "\n", $log ) );
        $lines = array_slice( array_values( $lines ), -100 );

        wp_send_json_success( [
            'log'   => implode( "\n", $lines ),
            'count' => count( $lines ),
        ] );
    }

    /**
     * AJAX: Test API connection.
     */
    public function ajax_test_connection() {
        check_ajax_referer( 'insight_seo_nonce', 'nonce' );

        if ( ! current_user_can( 'manage_options' ) ) {
            wp_send_json_error( [ 'message' => 'Permission denied.' ], 403 );
        }

        $api_keys = get_option( 'insight_seo_api_keys', [] );
        $settings = $this->get_settings();

        $results = [];

        // Test WordPress itself
        $results['wordpress'] = [
            'success' => true,
            'message' => 'WordPress ' . get_bloginfo( 'version' ) . ' — OK',
        ];

        // Test Claude API
        if ( ! empty( $api_keys['claude_key'] ) ) {
            $claude = new Insight_SEO_Claude_API( $api_keys['claude_key'], $settings['claude_model'] );
            $test   = $claude->test_connection();
            $results['claude'] = $test;
        } else {
            $results['claude'] = [
                'success' => false,
                'message' => 'Claude API key not configured.',
            ];
        }

        // Test Pexels API (basic connectivity check)
        if ( ! empty( $api_keys['pexels_key'] ) ) {
            $pexels_response = wp_remote_get( 'https://api.pexels.com/v1/search?query=nature&per_page=1', [
                'timeout' => 10,
                'headers' => [
                    'Authorization' => $api_keys['pexels_key'],
                ],
            ] );
            if ( is_wp_error( $pexels_response ) ) {
                $results['pexels'] = [ 'success' => false, 'message' => $pexels_response->get_error_message() ];
            } elseif ( wp_remote_retrieve_response_code( $pexels_response ) === 200 ) {
                $results['pexels'] = [ 'success' => true, 'message' => 'Pexels API — OK' ];
            } else {
                $results['pexels'] = [ 'success' => false, 'message' => 'HTTP ' . wp_remote_retrieve_response_code( $pexels_response ) ];
            }
        } else {
            $results['pexels'] = [
                'success' => false,
                'message' => 'Pexels API key not configured (images will be skipped).',
            ];
        }

        $all_success = $results['claude']['success'];

        wp_send_json_success( [
            'results' => $results,
            'overall' => $all_success,
            'message' => $all_success ? 'All critical connections OK.' : 'Some connections failed — check API keys.',
        ] );
    }

    /**
     * AJAX: Save agent settings.
     */
    public function ajax_save_settings() {
        check_ajax_referer( 'insight_seo_nonce', 'nonce' );

        if ( ! current_user_can( 'manage_options' ) ) {
            wp_send_json_error( [ 'message' => 'Permission denied.' ], 403 );
        }

        $settings = [
            'min_score'      => isset( $_POST['min_score'] ) ? max( 1, min( 100, (int) $_POST['min_score'] ) ) : 85,
            'cron_interval'  => isset( $_POST['cron_interval'] ) ? sanitize_text_field( wp_unslash( $_POST['cron_interval'] ) ) : 'every_five_minutes',
            'max_iterations' => isset( $_POST['max_iterations'] ) ? max( 1, min( 10, (int) $_POST['max_iterations'] ) ) : 3,
            'include_posts'  => ! empty( $_POST['include_posts'] ),
            'include_pages'  => ! empty( $_POST['include_pages'] ),
            'auto_publish'   => ! empty( $_POST['auto_publish'] ),
            'claude_model'   => isset( $_POST['claude_model'] ) ? sanitize_text_field( wp_unslash( $_POST['claude_model'] ) ) : 'claude-opus-4-7',
        ];

        // Validate cron interval
        $valid_intervals = [ 'every_five_minutes', 'every_ten_minutes', 'every_thirty_minutes', 'hourly' ];
        if ( ! in_array( $settings['cron_interval'], $valid_intervals, true ) ) {
            $settings['cron_interval'] = 'every_five_minutes';
        }

        // Validate model
        $valid_models = [ 'claude-opus-4-7', 'claude-sonnet-4-6', 'claude-haiku-4-5-20251001' ];
        if ( ! in_array( $settings['claude_model'], $valid_models, true ) ) {
            $settings['claude_model'] = 'claude-opus-4-7';
        }

        update_option( 'insight_seo_settings', $settings );

        // Reschedule cron with new interval
        wp_clear_scheduled_hook( 'insight_seo_cron' );
        wp_schedule_event( time(), $settings['cron_interval'], 'insight_seo_cron' );

        wp_send_json_success( [ 'message' => 'Settings saved successfully.' ] );
    }

    /**
     * AJAX: Save API keys.
     */
    public function ajax_save_api_keys() {
        check_ajax_referer( 'insight_seo_nonce', 'nonce' );

        if ( ! current_user_can( 'manage_options' ) ) {
            wp_send_json_error( [ 'message' => 'Permission denied.' ], 403 );
        }

        $existing = get_option( 'insight_seo_api_keys', [] );

        $claude_key = isset( $_POST['claude_key'] ) ? sanitize_text_field( wp_unslash( $_POST['claude_key'] ) ) : '';
        $pexels_key = isset( $_POST['pexels_key'] ) ? sanitize_text_field( wp_unslash( $_POST['pexels_key'] ) ) : '';

        // Only update if new value provided
        $api_keys = [
            'claude_key' => ! empty( $claude_key ) ? $claude_key : ( $existing['claude_key'] ?? '' ),
            'pexels_key' => ! empty( $pexels_key ) ? $pexels_key : ( $existing['pexels_key'] ?? '' ),
        ];

        update_option( 'insight_seo_api_keys', $api_keys );

        $claude_hint = ! empty( $api_keys['claude_key'] ) ? 'ends in ' . substr( $api_keys['claude_key'], -4 ) : 'not set';
        $pexels_hint = ! empty( $api_keys['pexels_key'] ) ? 'ends in ' . substr( $api_keys['pexels_key'], -4 ) : 'not set';

        wp_send_json_success( [
            'message'     => 'API keys saved.',
            'claude_hint' => $claude_hint,
            'pexels_hint' => $pexels_hint,
        ] );
    }

    /**
     * AJAX: Clear activity log.
     */
    public function ajax_clear_logs() {
        check_ajax_referer( 'insight_seo_nonce', 'nonce' );

        if ( ! current_user_can( 'manage_options' ) ) {
            wp_send_json_error( [ 'message' => 'Permission denied.' ], 403 );
        }

        update_option( 'insight_seo_activity_log', '', false );

        wp_send_json_success( [ 'message' => 'Logs cleared.', 'log' => '(Logs cleared.)' ] );
    }
}
