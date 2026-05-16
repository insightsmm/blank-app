<?php
/**
 * SEO Scorer — calculates a 0–100 SEO score for a WordPress post.
 *
 * @package Insight_SEO_Agent
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

class Insight_SEO_Scorer {

    /**
     * Calculate SEO score for a post.
     *
     * @param int $post_id
     * @return array{total: int, criteria: array, focus_keyword: string}
     */
    public function calculate( $post_id ) {
        $post = get_post( $post_id );
        if ( ! $post ) {
            return [ 'total' => 0, 'criteria' => [], 'focus_keyword' => '' ];
        }

        $title   = $post->post_title;
        $content = $post->post_content;
        $slug    = $post->post_name;

        // Detect focus keyword
        $keyword = $this->detect_focus_keyword( $post_id, $title, $content );

        $meta_desc  = $this->get_meta_desc( $post_id );
        $word_count = $this->word_count( $content );
        $kw_density = $this->keyword_density( $content, $keyword );

        $criteria = [];
        $total    = 0;

        // 1. Title contains focus keyword (15 pts)
        $passed = ! empty( $keyword ) && stripos( $title, $keyword ) !== false;
        $score  = $passed ? 15 : 0;
        $criteria[] = [
            'name'   => 'Title contains focus keyword',
            'score'  => $score,
            'max'    => 15,
            'passed' => $passed,
        ];
        $total += $score;

        // 2. Title length 50–60 chars (10 pts, partial 5 for 40–70)
        $title_len = mb_strlen( $title );
        if ( $title_len >= 50 && $title_len <= 60 ) {
            $score  = 10;
            $passed = true;
        } elseif ( $title_len >= 40 && $title_len <= 70 ) {
            $score  = 5;
            $passed = false;
        } else {
            $score  = 0;
            $passed = false;
        }
        $criteria[] = [
            'name'   => 'Title length 50–60 characters',
            'score'  => $score,
            'max'    => 10,
            'passed' => $passed,
        ];
        $total += $score;

        // 3. Meta description contains keyword (15 pts)
        $passed = ! empty( $keyword ) && ! empty( $meta_desc ) && stripos( $meta_desc, $keyword ) !== false;
        $score  = $passed ? 15 : 0;
        $criteria[] = [
            'name'   => 'Meta description contains focus keyword',
            'score'  => $score,
            'max'    => 15,
            'passed' => $passed,
        ];
        $total += $score;

        // 4. Meta description 150–160 chars (5 pts, partial 3 for 130–180)
        $meta_len = mb_strlen( $meta_desc );
        if ( $meta_len >= 150 && $meta_len <= 160 ) {
            $score  = 5;
            $passed = true;
        } elseif ( $meta_len >= 130 && $meta_len <= 180 ) {
            $score  = 3;
            $passed = false;
        } else {
            $score  = 0;
            $passed = false;
        }
        $criteria[] = [
            'name'   => 'Meta description 150–160 characters',
            'score'  => $score,
            'max'    => 5,
            'passed' => $passed,
        ];
        $total += $score;

        // 5. Content >= 600 words (15 pts, partial 8 for 300–599)
        if ( $word_count >= 600 ) {
            $score  = 15;
            $passed = true;
        } elseif ( $word_count >= 300 ) {
            $score  = 8;
            $passed = false;
        } else {
            $score  = 0;
            $passed = false;
        }
        $criteria[] = [
            'name'   => 'Content length >= 600 words',
            'score'  => $score,
            'max'    => 15,
            'passed' => $passed,
        ];
        $total += $score;

        // 6. Keyword density 1–3% (15 pts)
        $passed = $kw_density >= 1.0 && $kw_density <= 3.0;
        $score  = $passed ? 15 : 0;
        $criteria[] = [
            'name'   => 'Keyword density 1–3%',
            'score'  => $score,
            'max'    => 15,
            'passed' => $passed,
            'detail' => round( $kw_density, 2 ) . '%',
        ];
        $total += $score;

        // 7. H2/H3 headers in content (10 pts, partial 5 for just 1)
        preg_match_all( '/<h[23][^>]*>/i', $content, $headers );
        $header_count = count( $headers[0] );
        if ( $header_count >= 2 ) {
            $score  = 10;
            $passed = true;
        } elseif ( $header_count === 1 ) {
            $score  = 5;
            $passed = false;
        } else {
            $score  = 0;
            $passed = false;
        }
        $criteria[] = [
            'name'   => 'H2/H3 headers present in content',
            'score'  => $score,
            'max'    => 10,
            'passed' => $passed,
        ];
        $total += $score;

        // 8. Images with alt text (5 pts)
        preg_match_all( '/<img[^>]+alt=["\']([^"\']+)["\'][^>]*>/i', $content, $alts );
        $has_alt_img = ! empty( $alts[1] ) && ! empty( array_filter( $alts[1] ) );
        $score       = $has_alt_img ? 5 : 0;
        $criteria[] = [
            'name'   => 'Images have alt text',
            'score'  => $score,
            'max'    => 5,
            'passed' => $has_alt_img,
        ];
        $total += $score;

        // 9. Featured image set (5 pts)
        $has_thumb = has_post_thumbnail( $post_id );
        $score     = $has_thumb ? 5 : 0;
        $criteria[] = [
            'name'   => 'Featured image set',
            'score'  => $score,
            'max'    => 5,
            'passed' => $has_thumb,
        ];
        $total += $score;

        // 10. Slug contains keyword (5 pts)
        $kw_slug = str_replace( ' ', '-', strtolower( $keyword ) );
        $passed  = ! empty( $keyword ) && ! empty( $slug ) && stripos( $slug, $kw_slug ) !== false;
        $score   = $passed ? 5 : 0;
        $criteria[] = [
            'name'   => 'URL slug contains keyword',
            'score'  => $score,
            'max'    => 5,
            'passed' => $passed,
        ];
        $total += $score;

        return [
            'total'         => min( 100, $total ),
            'criteria'      => $criteria,
            'focus_keyword' => $keyword,
            'word_count'    => $word_count,
            'kw_density'    => round( $kw_density, 2 ),
        ];
    }

    /**
     * Detect focus keyword from Yoast meta, falling back to auto-detection.
     *
     * @param int    $post_id
     * @param string $title
     * @param string $content
     * @return string
     */
    private function detect_focus_keyword( $post_id, $title, $content ) {
        $yoast_kw = get_post_meta( $post_id, '_yoast_wpseo_focuskw', true );
        if ( ! empty( $yoast_kw ) ) {
            return sanitize_text_field( $yoast_kw );
        }

        $internal_kw = get_post_meta( $post_id, '_insight_seo_focus_keyword', true );
        if ( ! empty( $internal_kw ) ) {
            return sanitize_text_field( $internal_kw );
        }

        return $this->extract_keyword( $title, $content );
    }

    /**
     * Extract the most meaningful keyword from title + content.
     *
     * @param string $title
     * @param string $content
     * @return string
     */
    public function extract_keyword( $title, $content ) {
        $stopwords = [
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all',
            'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day',
            'get', 'has', 'him', 'his', 'how', 'its', 'let', 'may',
            'new', 'now', 'old', 'see', 'two', 'use', 'way', 'who',
            'did', 'yes', 'yet', 'any', 'big', 'say', 'she', 'too',
            'with', 'that', 'this', 'from', 'they', 'have', 'what',
            'been', 'when', 'your', 'more', 'also', 'into', 'will',
            'just', 'like', 'them', 'time', 'some', 'very', 'than',
            'then', 'each', 'much', 'only', 'most', 'such', 'made',
            'here', 'were', 'make', 'over', 'does', 'well', 'even',
            'back', 'good', 'many', 'word', 'know', 'take', 'where',
            'give', 'their', 'these', 'those', 'about', 'after',
            'could', 'other', 'being', 'while', 'should', 'because',
            'there', 'which', 'would', 'often', 'every', 'great',
            'post', 'page', 'content', 'wordpress',
        ];

        // Weight title more heavily
        $text = $title . ' ' . $title . ' ' . wp_strip_all_tags( $content );
        $text = strtolower( preg_replace( '/[^a-zA-Z\s]/', ' ', $text ) );

        $words = preg_split( '/\s+/', $text, -1, PREG_SPLIT_NO_EMPTY );
        $freq  = [];

        foreach ( $words as $word ) {
            if ( strlen( $word ) < 4 ) {
                continue;
            }
            if ( in_array( $word, $stopwords, true ) ) {
                continue;
            }
            $freq[ $word ] = isset( $freq[ $word ] ) ? $freq[ $word ] + 1 : 1;
        }

        if ( empty( $freq ) ) {
            return '';
        }

        arsort( $freq );
        $keys = array_keys( $freq );
        return (string) $keys[0];
    }

    /**
     * Count words in HTML content.
     *
     * @param string $html
     * @return int
     */
    public function word_count( $html ) {
        $text = wp_strip_all_tags( $html );
        $text = trim( preg_replace( '/\s+/', ' ', $text ) );
        if ( empty( $text ) ) {
            return 0;
        }
        return str_word_count( $text );
    }

    /**
     * Calculate keyword density (percentage).
     *
     * @param string $html
     * @param string $keyword
     * @return float
     */
    private function keyword_density( $html, $keyword ) {
        if ( empty( $keyword ) ) {
            return 0.0;
        }

        $text       = strtolower( wp_strip_all_tags( $html ) );
        $word_count = $this->word_count( $html );

        if ( $word_count === 0 ) {
            return 0.0;
        }

        $occurrences = substr_count( $text, strtolower( $keyword ) );
        return ( $occurrences / $word_count ) * 100;
    }

    /**
     * Get meta description for a post.
     *
     * @param int $post_id
     * @return string
     */
    public function get_meta_desc( $post_id ) {
        $yoast = get_post_meta( $post_id, '_yoast_wpseo_metadesc', true );
        if ( ! empty( $yoast ) ) {
            return (string) $yoast;
        }

        return (string) get_post_meta( $post_id, '_insight_seo_metadesc', true );
    }
}
