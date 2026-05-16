<?php
/**
 * Claude API Class
 * Handles communication with the Anthropic Claude API.
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

class Insight_SEO_Claude_API {

    /**
     * @var string API key
     */
    private $api_key;

    /**
     * @var string Model to use
     */
    private $model;

    /**
     * @var string API endpoint
     */
    const API_ENDPOINT = 'https://api.anthropic.com/v1/messages';

    /**
     * Constructor.
     *
     * @param string $api_key
     * @param string $model
     */
    public function __construct( $api_key, $model = 'claude-opus-4-7' ) {
        $this->api_key = $api_key;
        $this->model   = $model;
    }

    /**
     * Optimize post content for SEO.
     *
     * @param string $title
     * @param string $content_html
     * @param string $slug
     * @param string $focus_keyword
     * @return array|WP_Error
     */
    public function optimize_post( $title, $content_html, $slug, $focus_keyword = '' ) {
        $prompt = $this->build_optimization_prompt( $title, $content_html, $slug, $focus_keyword );

        $body = [
            'model'      => $this->model,
            'max_tokens' => 4096,
            'system'     => 'You are an expert SEO content optimizer. Return ONLY valid JSON, no markdown, no code fences, no explanations. The response must start with { and end with }.',
            'messages'   => [
                [
                    'role'    => 'user',
                    'content' => $prompt,
                ],
            ],
        ];

        $response = wp_remote_post( self::API_ENDPOINT, [
            'timeout' => 60,
            'headers' => [
                'x-api-key'         => $this->api_key,
                'anthropic-version' => '2023-06-01',
                'content-type'      => 'application/json',
            ],
            'body'    => wp_json_encode( $body ),
        ] );

        if ( is_wp_error( $response ) ) {
            return $response;
        }

        $http_code = wp_remote_retrieve_response_code( $response );
        $body_raw  = wp_remote_retrieve_body( $response );

        if ( $http_code !== 200 ) {
            $error_data = json_decode( $body_raw, true );
            $error_msg  = isset( $error_data['error']['message'] )
                ? $error_data['error']['message']
                : 'HTTP error ' . $http_code;
            return new WP_Error( 'claude_api_error', $error_msg, [ 'status' => $http_code ] );
        }

        $response_data = json_decode( $body_raw, true );

        if ( ! isset( $response_data['content'][0]['text'] ) ) {
            return new WP_Error( 'claude_parse_error', 'Unexpected API response structure' );
        }

        $text = trim( $response_data['content'][0]['text'] );

        // Strip markdown code fences if Claude added them anyway
        $text = preg_replace( '/^```(?:json)?\s*/i', '', $text );
        $text = preg_replace( '/\s*```\s*$/i', '', $text );
        $text = trim( $text );

        $decoded = json_decode( $text, true );

        if ( json_last_error() !== JSON_ERROR_NONE ) {
            // Try to extract JSON object from the text
            if ( preg_match( '/\{[\s\S]*\}/m', $text, $matches ) ) {
                $decoded = json_decode( $matches[0], true );
            }
        }

        if ( ! is_array( $decoded ) ) {
            return new WP_Error(
                'claude_json_error',
                'Failed to parse JSON from Claude response: ' . json_last_error_msg(),
                [ 'raw' => substr( $text, 0, 500 ) ]
            );
        }

        // Validate required keys
        $required = [ 'focus_keyword', 'optimized_title', 'meta_description', 'optimized_content', 'suggested_slug' ];
        foreach ( $required as $key ) {
            if ( ! isset( $decoded[ $key ] ) ) {
                return new WP_Error(
                    'claude_missing_key',
                    "Missing required key in Claude response: {$key}"
                );
            }
        }

        return $decoded;
    }

    /**
     * Build the SEO optimization prompt.
     *
     * @param string $title
     * @param string $content_html
     * @param string $slug
     * @param string $focus_keyword
     * @return string
     */
    private function build_optimization_prompt( $title, $content_html, $slug, $focus_keyword ) {
        // Truncate very long content to avoid token limits
        $content_preview = strlen( $content_html ) > 6000
            ? substr( $content_html, 0, 6000 ) . '...[content truncated]'
            : $content_html;

        return "Optimize this WordPress post for SEO. Return ONLY a valid JSON object with these exact keys:
- focus_keyword: string (1-3 word target keyword, most relevant to the content)
- optimized_title: string (50-60 chars, keyword near start, compelling and click-worthy)
- meta_description: string (150-160 chars, includes keyword and a call-to-action, no quotes)
- optimized_content: string (full HTML content with proper H2/H3 structure, keyword in first 100 words, keyword used naturally 2-3 times per 300 words, at least 600 words total, use <h2> and <h3> tags, use <p> tags for paragraphs, do NOT include images)
- suggested_slug: string (lowercase, hyphens only, keyword-based, no special chars)
- seo_notes: string (brief explanation of key changes made)

Current title: {$title}
Current slug: {$slug}
Current focus keyword: {$focus_keyword}

Content:
{$content_preview}

Remember: Return ONLY the JSON object, starting with { and ending with }. No markdown fences.";
    }

    /**
     * Test connection to the Claude API.
     *
     * @return bool|string True on success, error message on failure.
     */
    public function test_connection() {
        if ( empty( $this->api_key ) ) {
            return 'No API key provided';
        }

        $body = [
            'model'      => $this->model,
            'max_tokens' => 10,
            'messages'   => [
                [
                    'role'    => 'user',
                    'content' => 'Say: ok',
                ],
            ],
        ];

        $response = wp_remote_post( self::API_ENDPOINT, [
            'timeout' => 15,
            'headers' => [
                'x-api-key'         => $this->api_key,
                'anthropic-version' => '2023-06-01',
                'content-type'      => 'application/json',
            ],
            'body'    => wp_json_encode( $body ),
        ] );

        if ( is_wp_error( $response ) ) {
            return $response->get_error_message();
        }

        $http_code = wp_remote_retrieve_response_code( $response );

        if ( $http_code === 200 ) {
            return true;
        }

        $body_raw   = wp_remote_retrieve_body( $response );
        $error_data = json_decode( $body_raw, true );

        return isset( $error_data['error']['message'] )
            ? $error_data['error']['message']
            : 'HTTP error ' . $http_code;
    }
}
