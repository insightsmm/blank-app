<?php
/**
 * Pexels API — fetches images and uploads them to the WordPress media library.
 *
 * @package Insight_SEO_Agent
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

class Insight_SEO_Pexels_API {

    /** @var string */
    private $api_key;

    /** @var string */
    private $api_endpoint = 'https://api.pexels.com/v1/search';

    /**
     * Constructor.
     *
     * @param string $api_key Pexels API key.
     */
    public function __construct( $api_key ) {
        $this->api_key = sanitize_text_field( $api_key );
    }

    /**
     * Fetch an image from Pexels for a given query.
     *
     * @param string $query Search query.
     * @return array|null Array with url, photographer, alt on success; null on failure.
     */
    public function fetch_image( $query ) {
        if ( empty( $this->api_key ) ) {
            return null;
        }

        $url = add_query_arg( [
            'query'       => urlencode( $query ),
            'per_page'    => 5,
            'orientation' => 'landscape',
        ], $this->api_endpoint );

        $response = wp_remote_get( $url, [
            'timeout' => 30,
            'headers' => [
                'Authorization' => $this->api_key,
            ],
        ] );

        if ( is_wp_error( $response ) ) {
            return null;
        }

        $status_code = wp_remote_retrieve_response_code( $response );
        if ( $status_code !== 200 ) {
            return null;
        }

        $body = wp_remote_retrieve_body( $response );
        $data = json_decode( $body, true );

        if ( empty( $data['photos'] ) ) {
            return null;
        }

        // Use the first photo
        $photo = $data['photos'][0];

        $image_url    = isset( $photo['src']['large2x'] ) ? $photo['src']['large2x'] : $photo['src']['large'];
        $photographer = isset( $photo['photographer'] ) ? $photo['photographer'] : 'Pexels';

        return [
            'url'          => $image_url,
            'photographer' => $photographer,
            'alt'          => sanitize_text_field( $query ) . ' image',
            'pexels_id'    => $photo['id'],
        ];
    }

    /**
     * Upload an image from a URL to the WordPress media library.
     *
     * @param string $image_url  URL of the image to upload.
     * @param string $alt_text   Alt text for the image.
     * @param int    $post_id    Post ID to attach image to.
     * @return int|WP_Error Attachment ID on success, WP_Error on failure.
     */
    public function upload_to_wordpress( $image_url, $alt_text, $post_id ) {
        // Load WordPress media functions
        require_once ABSPATH . 'wp-admin/includes/file.php';
        require_once ABSPATH . 'wp-admin/includes/image.php';
        require_once ABSPATH . 'wp-admin/includes/media.php';

        // Download the image
        $response = wp_remote_get( $image_url, [
            'timeout'  => 60,
            'stream'   => false,
        ] );

        if ( is_wp_error( $response ) ) {
            return new WP_Error( 'download_failed', 'Failed to download image: ' . $response->get_error_message() );
        }

        $status_code = wp_remote_retrieve_response_code( $response );
        if ( $status_code !== 200 ) {
            return new WP_Error( 'download_failed', 'Image download returned HTTP ' . $status_code );
        }

        $image_data = wp_remote_retrieve_body( $response );

        if ( empty( $image_data ) ) {
            return new WP_Error( 'empty_image', 'Downloaded image is empty.' );
        }

        // Determine file extension from URL or content-type
        $extension  = $this->get_file_extension( $image_url, wp_remote_retrieve_header( $response, 'content-type' ) );
        $filename   = sanitize_file_name( 'pexels-' . time() . '.' . $extension );

        // Save to WP uploads
        $upload = wp_upload_bits( $filename, null, $image_data );

        if ( ! empty( $upload['error'] ) ) {
            return new WP_Error( 'upload_failed', 'wp_upload_bits failed: ' . $upload['error'] );
        }

        // Prepare attachment data
        $mime_types = [
            'jpg'  => 'image/jpeg',
            'jpeg' => 'image/jpeg',
            'png'  => 'image/png',
            'gif'  => 'image/gif',
            'webp' => 'image/webp',
        ];
        $mime_type = isset( $mime_types[ $extension ] ) ? $mime_types[ $extension ] : 'image/jpeg';

        $attachment = [
            'guid'           => $upload['url'],
            'post_mime_type' => $mime_type,
            'post_title'     => sanitize_text_field( $alt_text ),
            'post_content'   => '',
            'post_status'    => 'inherit',
        ];

        $attach_id = wp_insert_attachment( $attachment, $upload['file'], $post_id );

        if ( is_wp_error( $attach_id ) ) {
            return $attach_id;
        }

        // Generate attachment metadata (thumbnails etc.)
        $attach_data = wp_generate_attachment_metadata( $attach_id, $upload['file'] );
        wp_update_attachment_metadata( $attach_id, $attach_data );

        // Set alt text
        update_post_meta( $attach_id, '_wp_attachment_image_alt', sanitize_text_field( $alt_text ) );

        // Add photographer credit as caption
        update_post_meta( $attach_id, '_wp_attachment_image_caption', 'Photo from Pexels' );

        return $attach_id;
    }

    /**
     * Determine file extension from URL or content-type header.
     *
     * @param string $url          Image URL.
     * @param string $content_type Content-Type header value.
     * @return string File extension (without dot).
     */
    private function get_file_extension( $url, $content_type ) {
        // Try from URL
        $path_parts = pathinfo( wp_parse_url( $url, PHP_URL_PATH ) );
        if ( ! empty( $path_parts['extension'] ) ) {
            $ext = strtolower( $path_parts['extension'] );
            // Strip query string remnants
            $ext = preg_replace( '/\?.*/', '', $ext );
            if ( in_array( $ext, [ 'jpg', 'jpeg', 'png', 'gif', 'webp' ], true ) ) {
                return $ext;
            }
        }

        // Try from content-type
        $ct_map = [
            'image/jpeg' => 'jpg',
            'image/png'  => 'png',
            'image/gif'  => 'gif',
            'image/webp' => 'webp',
        ];
        foreach ( $ct_map as $ct => $ext ) {
            if ( strpos( $content_type, $ct ) !== false ) {
                return $ext;
            }
        }

        return 'jpg';
    }
}
