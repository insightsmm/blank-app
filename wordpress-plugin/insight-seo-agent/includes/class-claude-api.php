<?php
/**
 * Claude API — communicates with the Anthropic Claude API to optimise post content for SEO.
 *
 * @package Insight_SEO_Agent
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

class Insight_SEO_Claude_API {

    /** @var string */
    private $api_key;

    /** @var string */
    private $model;

    /** @var string */
    private $api_endpoint = 'https://api.anthropic.com/v1/messages';

    /**
     * Constructor.
     *
     * @param string $api_key  Anthropic API key.
     * @param string $model    Claude model identifier.
     */
    public function __construct( $api_key, $model = 'claude-opus-4-7' ) {
        $this->api_key = sanitize_text_field( $api_key );
        $this->model   = sanitize_text_field( $model );
    }

    /**
     * Optimize a WordPress post for SEO using Claude.
     *
     * @param string $title           Post title.
     * @param string $content_html    Post content (HTML).
     * @param string $slug            Post slug.
     * @param string $focus_keyword   Optional current focus keyword.
     * @return array|WP_Error Decoded JSON array or WP_Error on failure.
     */
    public function optimize_post( $title, $content_html, $slug, $focus_keyword = '' ) {
        if ( empty( $this->api_key ) ) {
            return new WP_Error( 'no_api_key', 'Claude API key is not configured.' );
        }

        $prompt = $this->build_seo_prompt( $title, $content_html, $slug, $focus_keyword );

        $response = wp_remote_post( $this->api_endpoint, [
            'timeout' => 90,
            'headers' => [
                'x-api-key'         => $this->api_key,
                'anthropic-version' => '2023-06-01',
                'content-type'      => 'application/json',
            ],
            'body' => wp_json_encode( [
                'model'      => $this->model,
                'max_tokens' => 4096,
                'system'     => 'You are an expert SEO content optimizer. Return ONLY valid JSON, no markdown fences, no explanation — just the raw JSON object.',
                'messages'   => [
                    [
                        'role'    => 'user',
                        'content' => $prompt,
                    ],
                ],
            ] ),
        ] );

        if ( is_wp_error( $response ) ) {
            return new WP_Error(
                'api_request_failed',
                'Claude API request failed: ' . $response->get_error_message()
            );
        }

        $status_code = wp_remote_retrieve_response_code( $response );
        $body        = wp_remote_retrieve_body( $response );

        if ( $status_code !== 200 ) {
            $error_data = json_decode( $body, true );
            $error_msg  = isset( $error_data['error']['message'] )
                ? $error_data['error']['message']
                : 'HTTP ' . $status_code;
            return new WP_Error( 'api_error', 'Claude API error: ' . $error_msg );
        }

        $response_data = json_decode( $body, true );

        if ( ! isset( $response_data['content'][0]['text'] ) ) {
            return new WP_Error( 'invalid_response', 'Unexpected Claude API response format.' );
        }

        $text = trim( $response_data['content'][0]['text'] );

        // Strip markdown code fences if present
        $text = preg_replace( '/^```(?:json)?\s*/i', '', $text );
        $text = preg_replace( '/\s*```$/', '', $text );
        $text = trim( $text );

        $decoded = json_decode( $text, true );

        if ( json_last_error() !== JSON_ERROR_NONE ) {
            return new WP_Error(
                'json_parse_error',
                'Failed to parse Claude response as JSON: ' . json_last_error_msg() . '. Raw: ' . substr( $text, 0, 300 )
            );
        }

        // Validate required keys
        $required_keys = [ 'focus_keyword', 'optimized_title', 'meta_description', 'optimized_content' ];
        foreach ( $required_keys as $key ) {
            if ( ! isset( $decoded[ $key ] ) ) {
                return new WP_Error( 'missing_key', "Claude response missing required key: {$key}" );
            }
        }

        return $decoded;
    }

    /**
     * Build the SEO optimisation prompt.
     *
     * @param string $title
     * @param string $content_html
     * @param string $slug
     * @param string $focus_keyword
     * @return string
     */
    private function build_seo_prompt( $title, $content_html, $slug, $focus_keyword ) {
        // Truncate content if very long to stay within token limits
        $max_content_chars = 6000;
        if ( strlen( $content_html ) > $max_content_chars ) {
            $content_html = substr( $content_html, 0, $max_content_chars ) . '... [content truncated]';
        }

        return "Optimize this WordPress post for SEO. Return ONLY a valid JSON object with these exact keys (no markdown, no extra text):

{
  \"focus_keyword\": \"(1-3 word target keyword)\",
  \"optimized_title\": \"(50-60 chars, keyword near start)\",
  \"meta_description\": \"(150-160 chars, includes keyword and a call-to-action)\",
  \"optimized_content\": \"(full HTML content with proper H2/H3 structure, keyword in first 100 words, keyword used naturally 2-3x per 300 words, at least 600 words total)\",
  \"suggested_slug\": \"(lowercase, hyphens, keyword-based, no stop words)\",
  \"seo_notes\": \"(brief explanation of key changes made)\"
}

Requirements for optimized_content:
- Must be valid HTML with proper paragraph tags
- Include at least 2 H2 or H3 subheadings
- At least 600 words
- Use the focus keyword naturally 2-3 times per 300 words
- Include the focus keyword within the first 100 words
- Do NOT use markdown — use HTML tags only

Current title: " . $title . "
Current slug: " . $slug . "
Current focus keyword: " . ( $focus_keyword ?: '(not set — please determine the best keyword)' ) . "

Current content:
" . $content_html;
    }

    /**
     * Test the Claude API connection.
     *
     * @return array{success: bool, message: string}
     */
    public function test_connection() {
        if ( empty( $this->api_key ) ) {
            return [ 'success' => false, 'message' => 'API key not configured.' ];
        }

        $response = wp_remote_post( $this->api_endpoint, [
            'timeout' => 30,
            'headers' => [
                'x-api-key'         => $this->api_key,
                'anthropic-version' => '2023-06-01',
                'content-type'      => 'application/json',
            ],
            'body' => wp_json_encode( [
                'model'      => $this->model,
                'max_tokens' => 10,
                'messages'   => [
                    [
                        'role'    => 'user',
                        'content' => 'Say: ok',
                    ],
                ],
            ] ),
        ] );

        if ( is_wp_error( $response ) ) {
            return [
                'success' => false,
                'message' => 'Connection failed: ' . $response->get_error_message(),
            ];
        }

        $status_code = wp_remote_retrieve_response_code( $response );

        if ( $status_code === 200 ) {
            $body = wp_remote_retrieve_body( $response );
            $data = json_decode( $body, true );
            $text = isset( $data['content'][0]['text'] ) ? $data['content'][0]['text'] : 'Connected';
            return [
                'success' => true,
                'message' => 'Claude API connected. Response: ' . $text,
            ];
        }

        $body      = wp_remote_retrieve_body( $response );
        $error     = json_decode( $body, true );
        $error_msg = isset( $error['error']['message'] ) ? $error['error']['message'] : 'HTTP ' . $status_code;

        return [
            'success' => false,
            'message' => 'API error: ' . $error_msg,
        ];
    }
}
