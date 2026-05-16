<?php
/**
 * Pexels API Class
 * Handles fetching and uploading images from Pexels.
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

class Insight_SEO_Pexels_API {

    /**
     * @var string API key
     */
    private $api_key;

    /**
     * @var string API endpoint
     */
    const API_ENDPOINT = 'https://api.pexels.com/v1/search';

    /**
     * Constructor.
     *
     * @param string $api_key
     */
    public function __construct( $api_key ) {
        $this->api_key = $api_key;
    }

    /**
     * Fetch an image from Pexels based on a search query.
     *
     * @param string $query
     * @return array|null Array with url, photographer, alt keys, or null on failure.
     */
    public function fetch_image( $query ) {
        if ( empty( $this->api_key ) ) {
            return null;
        }

        $url = add_query_arg( [
            'query'       => urlencode( $query ),
            'per_page'    => 5,
            'orientation' => 'landscape',
        ], self::API_ENDPOINT );

        $response = wp_remote_get( $url, [
            'timeout' => 20,
            'headers' => [
                'Authorization' => $this->api_key,
            ],
        ] );

        if ( is_wp_error( $response ) ) {
            return null;
        }

        $http_code = wp_remote_retrieve_response_code( $response );
        if ( $http_code !== 200 ) {
            return null;
        }

        $body = wp_remote_retrieve_body( $response );
        $data = json_decode( $body, true );

        if ( empty( $data['photos'] ) || ! is_array( $data['photos'] ) ) {
            return null;
        }

        // Pick the first suitable photo
        foreach ( $data['photos'] as $photo ) {
            if ( ! empty( $photo['src']['large2x'] ) ) {
                return [
                    'url'          => $photo['src']['large2x'],
                    'photographer' => $photo['photographer'] ?? 'Pexels',
                    'alt'          => $query . ' image',
                    'pexels_url'   => $photo['url'] ?? '',
                ];
            }
        }

        return null;
    }

    /**
     * Download a Pexels image and upload it to the WordPress media library.
     *
     * @param string $image_url
     * @param string $alt_text
     * @param int    $post_id
     * @return int|WP_Error Attachment ID on success, WP_Error on failure.
     */
    public function upload_to_wordpress( $image_url, $alt_text, $post_id ) {
        // Make sure we have media handling functions
        if ( ! function_exists( 'wp_insert_attachment' ) ) {
            require_once ABSPATH . 'wp-admin/includes/image.php';
            require_once ABSPATH . 'wp-admin/includes/file.php';
            require_once ABSPATH . 'wp-admin/includes/media.php';
        }

        // Download the image
        $response = wp_remote_get( $image_url, [
            'timeout' => 30,
        ] );

        if ( is_wp_error( $response ) ) {
            return $response;
        }

        $http_code = wp_remote_retrieve_response_code( $response );
        if ( $http_code !== 200 ) {
            return new WP_Error( 'pexels_download_failed', 'Failed to download image, HTTP ' . $http_code );
        }

        $image_data = wp_remote_retrieve_body( $response );
        if ( empty( $image_data ) ) {
            return new WP_Error( 'pexels_empty_response', 'Empty image response from Pexels' );
        }

        // Determine file extension from URL
        $url_path = wp_parse_url( $image_url, PHP_URL_PATH );
        $ext      = strtolower( pathinfo( $url_path, PATHINFO_EXTENSION ) );
        if ( ! in_array( $ext, [ 'jpg', 'jpeg', 'png', 'gif', 'webp' ], true ) ) {
            // Check content type
            $content_type = wp_remote_retrieve_header( $response, 'content-type' );
            $mime_to_ext  = [
                'image/jpeg' => 'jpg',
                'image/png'  => 'png',
                'image/gif'  => 'gif',
                'image/webp' => 'webp',
            ];
            $ext = $mime_to_ext[ $content_type ] ?? 'jpg';
        }

        // Create a sanitized filename
        $filename = sanitize_file_name( $alt_text . '.' . $ext );

        // Save to uploads directory using wp_upload_bits
        $upload = wp_upload_bits( $filename, null, $image_data );
        if ( ! empty( $upload['error'] ) ) {
            return new WP_Error( 'pexels_upload_bits_failed', $upload['error'] );
        }

        $file_path = $upload['file'];
        $file_url  = $upload['url'];
        $file_type = wp_check_filetype( $filename, null );

        // Prepare attachment data
        $attachment = [
            'guid'           => $file_url,
            'post_mime_type' => $file_type['type'],
            'post_title'     => sanitize_text_field( $alt_text ),
            'post_content'   => '',
            'post_status'    => 'inherit',
        ];

        // Insert attachment into media library
        $attach_id = wp_insert_attachment( $attachment, $file_path, $post_id );
        if ( is_wp_error( $attach_id ) ) {
            return $attach_id;
        }

        // Generate attachment metadata
        require_once ABSPATH . 'wp-admin/includes/image.php';
        $attach_data = wp_generate_attachment_metadata( $attach_id, $file_path );
        wp_update_attachment_metadata( $attach_id, $attach_data );

        // Set alt text
        update_post_meta( $attach_id, '_wp_attachment_image_alt', sanitize_text_field( $alt_text ) );

        return $attach_id;
    }
}
