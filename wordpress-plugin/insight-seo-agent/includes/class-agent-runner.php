<?php
/**
 * Agent Runner — orchestrates the full SEO optimization pipeline.
 *
 * @package Insight_SEO_Agent
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

class Insight_SEO_Agent_Runner {

    /** @var array */
    private $settings;

    /** @var Insight_SEO_Scorer */
    private $scorer;

    /** @var Insight_SEO_Claude_API|null */
    private $claude;

    /** @var Insight_SEO_Pexels_API|null */
    private $pexels;

    /**
     * Constructor — reads settings and instantiates API classes.
     */
    public function __construct() {
        $defaults       = function_exists( 'insight_seo_default_settings' )
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

        $this->settings = wp_parse_args(
            get_option( 'insight_seo_settings', [] ),
            $defaults
        );

        $this->scorer = new Insight_SEO_Scorer();

        // Load API keys
        $api_keys    = get_option( 'insight_seo_api_keys', [] );
        $claude_key  = ! empty( $api_keys['claude_key'] ) ? $api_keys['claude_key'] : '';
        $pexels_key  = ! empty( $api_keys['pexels_key'] ) ? $api_keys['pexels_key'] : '';
        $claude_model = isset( $this->settings['claude_model'] ) ? $this->settings['claude_model'] : 'claude-opus-4-7';

        $this->claude = ! empty( $claude_key )
            ? new Insight_SEO_Claude_API( $claude_key, $claude_model )
            : null;

        $this->pexels = ! empty( $pexels_key )
            ? new Insight_SEO_Pexels_API( $pexels_key )
            : null;
    }

    /**
     * Process all draft posts/pages.
     *
     * @return array Summary of processing results.
     */
    public function process_all_drafts() {
        $post_types = [];
        if ( ! empty( $this->settings['include_posts'] ) ) {
            $post_types[] = 'post';
        }
        if ( ! empty( $this->settings['include_pages'] ) ) {
            $post_types[] = 'page';
        }

        if ( empty( $post_types ) ) {
            $this->log_message( 'Agent cycle: no post types configured — skipping.' );
            return [ 'processed' => 0, 'published' => 0, 'failed' => 0, 'skipped' => 0 ];
        }

        $drafts = get_posts( [
            'post_status'    => 'draft',
            'post_type'      => $post_types,
            'posts_per_page' => 20,
            'orderby'        => 'date',
            'order'          => 'ASC',
            'fields'         => 'ids',
        ] );

        $summary = [
            'processed' => 0,
            'published' => 0,
            'failed'    => 0,
            'skipped'   => 0,
        ];

        if ( empty( $drafts ) ) {
            $this->log_message( 'Agent cycle: no draft posts found.' );
            return $summary;
        }

        $this->log_message( 'Agent cycle started — found ' . count( $drafts ) . ' draft(s).' );

        foreach ( $drafts as $post_id ) {
            $result = $this->run_on_post( $post_id );

            if ( isset( $result['status'] ) ) {
                switch ( $result['status'] ) {
                    case 'published':
                        $summary['published']++;
                        $summary['processed']++;
                        break;
                    case 'processing':
                    case 'optimized':
                        $summary['processed']++;
                        break;
                    case 'failed':
                        $summary['failed']++;
                        break;
                    case 'skipped':
                        $summary['skipped']++;
                        break;
                }
            }
        }

        $this->log_message(
            sprintf(
                'Agent cycle complete — processed: %d, published: %d, failed: %d, skipped: %d.',
                $summary['processed'],
                $summary['published'],
                $summary['failed'],
                $summary['skipped']
            )
        );

        return $summary;
    }

    /**
     * Run the full SEO optimization pipeline on a single post.
     *
     * @param int $post_id
     * @return array Result array with status, scores, iterations.
     */
    public function run_on_post( $post_id ) {
        $post = get_post( $post_id );

        if ( ! $post ) {
            return [ 'status' => 'failed', 'error' => 'Post not found.' ];
        }

        // Skip already-published posts
        if ( $post->post_status === 'publish' ) {
            return [ 'status' => 'skipped', 'reason' => 'Post already published.' ];
        }

        // Check if Claude API is available
        if ( ! $this->claude ) {
            $this->log_message( "Skipped '{$post->post_title}' (ID: {$post_id}) — Claude API key not configured." );
            return [ 'status' => 'skipped', 'reason' => 'Claude API key not configured.' ];
        }

        // Calculate initial SEO score
        $initial_score_data = $this->scorer->calculate( $post_id );
        $score_before       = $initial_score_data['total'];

        $this->log_message(
            "Starting SEO optimization for '{$post->post_title}' (ID: {$post_id}), initial score: {$score_before}/100."
        );

        $min_score     = isset( $this->settings['min_score'] ) ? (int) $this->settings['min_score'] : 85;
        $max_iterations = isset( $this->settings['max_iterations'] ) ? (int) $this->settings['max_iterations'] : 3;
        $auto_publish  = ! empty( $this->settings['auto_publish'] );

        $current_score = $score_before;
        $iterations    = 0;
        $last_error    = '';
        $notes         = [];

        // Optimization loop
        while ( $current_score < $min_score && $iterations < $max_iterations ) {
            $iterations++;
            $this->log_message( "  Iteration {$iterations}/{$max_iterations} for post ID {$post_id}..." );

            // Reload post (may have been updated)
            $post = get_post( $post_id );

            // Call Claude API
            $result = $this->claude->optimize_post(
                $post->post_title,
                $post->post_content,
                $post->post_name,
                $initial_score_data['focus_keyword']
            );

            if ( is_wp_error( $result ) ) {
                $last_error = $result->get_error_message();
                $this->log_message( "  Claude API error: {$last_error}" );
                break;
            }

            // Extract optimized fields
            $optimized_title   = isset( $result['optimized_title'] ) ? sanitize_text_field( $result['optimized_title'] ) : $post->post_title;
            $meta_description  = isset( $result['meta_description'] ) ? sanitize_text_field( $result['meta_description'] ) : '';
            $optimized_content = isset( $result['optimized_content'] ) ? wp_kses_post( $result['optimized_content'] ) : $post->post_content;
            $focus_keyword     = isset( $result['focus_keyword'] ) ? sanitize_text_field( $result['focus_keyword'] ) : $initial_score_data['focus_keyword'];
            $suggested_slug    = isset( $result['suggested_slug'] ) ? sanitize_title( $result['suggested_slug'] ) : $post->post_name;
            $seo_notes         = isset( $result['seo_notes'] ) ? sanitize_text_field( $result['seo_notes'] ) : '';

            if ( ! empty( $seo_notes ) ) {
                $notes[] = "Iter {$iterations}: {$seo_notes}";
            }

            // Handle Pexels image before updating content
            $content_to_save = $optimized_content;

            if ( $this->pexels ) {
                // Only add image if no featured image set
                if ( ! has_post_thumbnail( $post_id ) ) {
                    $image_query    = $focus_keyword . ' ' . implode( ' ', array_slice( explode( ' ', $post->post_title ), 0, 3 ) );
                    $pexels_image   = $this->pexels->fetch_image( $image_query );

                    if ( $pexels_image ) {
                        $this->log_message( "  Fetching Pexels image for query: '{$image_query}'..." );
                        $attach_id = $this->pexels->upload_to_wordpress(
                            $pexels_image['url'],
                            $pexels_image['alt'],
                            $post_id
                        );

                        if ( ! is_wp_error( $attach_id ) ) {
                            set_post_thumbnail( $post_id, $attach_id );
                            $this->log_message( "  Set featured image (attachment ID: {$attach_id})." );

                            // Insert inline image if content has no images
                            if ( strpos( $content_to_save, '<img' ) === false ) {
                                $img_url         = wp_get_attachment_url( $attach_id );
                                $content_to_save = $this->insert_inline_image( $content_to_save, $img_url, $pexels_image['alt'] );
                            }
                        } else {
                            $this->log_message( '  Pexels upload failed: ' . $attach_id->get_error_message() );
                        }
                    }
                }
            }

            // Update the post (disable kses filtering during update to preserve HTML)
            remove_filter( 'content_save_pre', 'wp_filter_post_kses' );
            remove_filter( 'content_filtered_save_pre', 'wp_filter_post_kses' );

            $update_result = wp_update_post( [
                'ID'           => $post_id,
                'post_title'   => $optimized_title,
                'post_content' => $content_to_save,
                'post_name'    => $suggested_slug,
            ], true );

            add_filter( 'content_save_pre', 'wp_filter_post_kses' );
            add_filter( 'content_filtered_save_pre', 'wp_filter_post_kses' );

            if ( is_wp_error( $update_result ) ) {
                $last_error = $update_result->get_error_message();
                $this->log_message( "  wp_update_post failed: {$last_error}" );
                break;
            }

            // Update Yoast SEO meta
            update_post_meta( $post_id, '_yoast_wpseo_focuskw', $focus_keyword );
            update_post_meta( $post_id, '_yoast_wpseo_title', $optimized_title );
            update_post_meta( $post_id, '_yoast_wpseo_metadesc', $meta_description );

            // Internal fallback meta
            update_post_meta( $post_id, '_insight_seo_metadesc', $meta_description );
            update_post_meta( $post_id, '_insight_seo_focus_keyword', $focus_keyword );

            // Recalculate SEO score
            $score_data    = $this->scorer->calculate( $post_id );
            $current_score = $score_data['total'];

            $this->log_message(
                "  After iteration {$iterations}: SEO score = {$current_score}/100, keyword = '{$focus_keyword}'."
            );
        }

        // Mark as processed
        update_post_meta( $post_id, '_insight_seo_processed', current_time( 'mysql' ) );
        update_post_meta( $post_id, '_insight_seo_score', $current_score );
        delete_post_meta( $post_id, '_insight_seo_queued' );

        // Determine final status
        $status = 'processing';

        if ( ! empty( $last_error ) && $iterations === 0 ) {
            $status = 'failed';
        } elseif ( $current_score >= $min_score && $auto_publish ) {
            // Publish the post
            wp_update_post( [
                'ID'          => $post_id,
                'post_status' => 'publish',
            ] );
            $status = 'published';
            $this->log_message( "Published '{$post->post_title}' (ID: {$post_id}) with SEO score {$current_score}/100." );
        } else {
            $status = $current_score >= $min_score ? 'optimized' : 'processing';
            $this->log_message(
                "Post '{$post->post_title}' (ID: {$post_id}) score: {$current_score}/100. " .
                ( $current_score < $min_score ? "Score below threshold ({$min_score}), not published." : 'Auto-publish disabled.' )
            );
        }

        // Insert log row into DB
        global $wpdb;
        $table = $wpdb->prefix . 'insight_seo_log';

        $wpdb->insert(
            $table,
            [
                'post_id'         => $post_id,
                'post_title'      => $post->post_title,
                'post_type'       => $post->post_type,
                'seo_score_before' => $score_before,
                'seo_score_after'  => $current_score,
                'status'          => $status,
                'iterations'      => $iterations,
                'processed_at'    => current_time( 'mysql' ),
                'notes'           => implode( ' | ', $notes ),
            ],
            [
                '%d', '%s', '%s', '%d', '%d', '%s', '%d', '%s', '%s',
            ]
        );

        return [
            'status'       => $status,
            'post_id'      => $post_id,
            'post_title'   => $post->post_title,
            'score_before' => $score_before,
            'score_after'  => $current_score,
            'iterations'   => $iterations,
            'error'        => $last_error,
        ];
    }

    /**
     * Insert an inline image after the first closing </p> tag in content.
     *
     * @param string $content   Post content HTML.
     * @param string $img_url   Image URL.
     * @param string $alt_text  Image alt text.
     * @return string Modified content.
     */
    public function insert_inline_image( $content, $img_url, $alt_text ) {
        // Don't insert if content already has an image
        if ( strpos( $content, '<img' ) !== false ) {
            return $content;
        }

        $img_html = sprintf(
            '<figure class="wp-block-image size-large"><img src="%s" alt="%s" class="wp-image" /></figure>',
            esc_url( $img_url ),
            esc_attr( $alt_text )
        );

        // Find position after the first </p>
        $pos = strpos( $content, '</p>' );
        if ( $pos !== false ) {
            return substr_replace( $content, '</p>' . $img_html, $pos, 4 );
        }

        // If no <p> found, prepend image
        return $img_html . $content;
    }

    /**
     * Append a timestamped message to the activity log option.
     * Keeps the last 200 lines.
     *
     * @param string $msg
     */
    public function log_message( $msg ) {
        $timestamp   = current_time( 'Y-m-d H:i:s' );
        $new_entry   = "[{$timestamp}] {$msg}";
        $current_log = get_option( 'insight_seo_activity_log', '' );

        $lines = array_filter( explode( "\n", $current_log ) );
        $lines = array_values( $lines );
        $lines[] = $new_entry;

        // Keep last 200 lines
        if ( count( $lines ) > 200 ) {
            $lines = array_slice( $lines, -200 );
        }

        update_option( 'insight_seo_activity_log', implode( "\n", $lines ), false );
    }
}
