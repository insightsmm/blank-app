<?php
/**
 * SEO Scorer Class
 * Calculates SEO score for a WordPress post based on 10 criteria.
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

class Insight_SEO_Scorer {

    /**
     * Calculate SEO score for a post.
     *
     * @param int $post_id
     * @return array
     */
    public function calculate( $post_id ) {
        $post = get_post( $post_id );
        if ( ! $post ) {
            return [ 'total' => 0, 'criteria' => [], 'focus_keyword' => '' ];
        }

        $title   = $post->post_title;
        $content = $post->post_content;
        $slug    = $post->post_name;

        // Determine focus keyword
        $focus_keyword = get_post_meta( $post_id, '_yoast_wpseo_focuskw', true );
        if ( empty( $focus_keyword ) ) {
            $focus_keyword = $this->extract_keyword( $title, $content );
        }

        $meta_desc   = $this->get_meta_desc( $post_id );
        $word_count  = $this->word_count( $content );
        $title_len   = strlen( $title );
        $meta_len    = strlen( $meta_desc );

        $criteria = [];
        $total    = 0;

        // 1. Title contains focus keyword (15 pts)
        $passed = ! empty( $focus_keyword ) && stripos( $title, $focus_keyword ) !== false;
        $score  = $passed ? 15 : 0;
        $total += $score;
        $criteria[] = [
            'name'   => 'Title contains focus keyword',
            'score'  => $score,
            'max'    => 15,
            'passed' => $passed,
        ];

        // 2. Title length 50–60 chars (10 pts, partial 5 pts for 40–70)
        if ( $title_len >= 50 && $title_len <= 60 ) {
            $score = 10;
        } elseif ( $title_len >= 40 && $title_len <= 70 ) {
            $score = 5;
        } else {
            $score = 0;
        }
        $total += $score;
        $criteria[] = [
            'name'   => 'Title length 50–60 chars',
            'score'  => $score,
            'max'    => 10,
            'passed' => ( $title_len >= 50 && $title_len <= 60 ),
            'detail' => $title_len . ' chars',
        ];

        // 3. Meta description with keyword (15 pts)
        $passed = ! empty( $focus_keyword ) && ! empty( $meta_desc ) && stripos( $meta_desc, $focus_keyword ) !== false;
        $score  = $passed ? 15 : 0;
        $total += $score;
        $criteria[] = [
            'name'   => 'Meta description contains keyword',
            'score'  => $score,
            'max'    => 15,
            'passed' => $passed,
        ];

        // 4. Meta description 150–160 chars (5 pts, partial 3 pts for 130–180)
        if ( $meta_len >= 150 && $meta_len <= 160 ) {
            $score = 5;
        } elseif ( $meta_len >= 130 && $meta_len <= 180 ) {
            $score = 3;
        } else {
            $score = 0;
        }
        $total += $score;
        $criteria[] = [
            'name'   => 'Meta description length 150–160 chars',
            'score'  => $score,
            'max'    => 5,
            'passed' => ( $meta_len >= 150 && $meta_len <= 160 ),
            'detail' => $meta_len . ' chars',
        ];

        // 5. Content ≥ 600 words (15 pts, partial 8 pts for 300–599)
        if ( $word_count >= 600 ) {
            $score = 15;
        } elseif ( $word_count >= 300 ) {
            $score = 8;
        } else {
            $score = 0;
        }
        $total += $score;
        $criteria[] = [
            'name'   => 'Content length ≥ 600 words',
            'score'  => $score,
            'max'    => 15,
            'passed' => $word_count >= 600,
            'detail' => $word_count . ' words',
        ];

        // 6. Keyword density 1–3% (15 pts)
        $density = 0;
        if ( ! empty( $focus_keyword ) && $word_count > 0 ) {
            $plain_content = strtolower( strip_tags( $content ) );
            $keyword_lower = strtolower( $focus_keyword );
            $occurrences   = substr_count( $plain_content, $keyword_lower );
            $density       = ( $occurrences / $word_count ) * 100;
        }
        $passed = $density >= 1 && $density <= 3;
        $score  = $passed ? 15 : 0;
        $total += $score;
        $criteria[] = [
            'name'   => 'Keyword density 1–3%',
            'score'  => $score,
            'max'    => 15,
            'passed' => $passed,
            'detail' => round( $density, 2 ) . '%',
        ];

        // 7. H2/H3 headers in content (10 pts, partial 5 pts for 1 header)
        preg_match_all( '/<h[23][^>]*>/i', $content, $header_matches );
        $header_count = count( $header_matches[0] );
        if ( $header_count >= 2 ) {
            $score = 10;
        } elseif ( $header_count === 1 ) {
            $score = 5;
        } else {
            $score = 0;
        }
        $total += $score;
        $criteria[] = [
            'name'   => 'H2/H3 headers present',
            'score'  => $score,
            'max'    => 10,
            'passed' => $header_count >= 2,
            'detail' => $header_count . ' headers found',
        ];

        // 8. Images with alt text (5 pts)
        preg_match_all( '/<img[^>]+>/i', $content, $img_matches );
        $imgs_with_alt = 0;
        foreach ( $img_matches[0] as $img_tag ) {
            if ( preg_match( '/alt=["\']([^"\']+)["\']/i', $img_tag ) ) {
                $imgs_with_alt++;
            }
        }
        $passed = $imgs_with_alt > 0;
        $score  = $passed ? 5 : 0;
        $total += $score;
        $criteria[] = [
            'name'   => 'Images with alt text',
            'score'  => $score,
            'max'    => 5,
            'passed' => $passed,
            'detail' => $imgs_with_alt . ' image(s) with alt',
        ];

        // 9. Featured image set (5 pts)
        $passed = has_post_thumbnail( $post_id );
        $score  = $passed ? 5 : 0;
        $total += $score;
        $criteria[] = [
            'name'   => 'Featured image set',
            'score'  => $score,
            'max'    => 5,
            'passed' => $passed,
        ];

        // 10. Slug contains keyword (5 pts)
        $keyword_slug = ! empty( $focus_keyword ) ? str_replace( ' ', '-', strtolower( $focus_keyword ) ) : '';
        $passed       = ! empty( $keyword_slug ) && stripos( $slug, $keyword_slug ) !== false;
        $score        = $passed ? 5 : 0;
        $total += $score;
        $criteria[] = [
            'name'   => 'Slug contains keyword',
            'score'  => $score,
            'max'    => 5,
            'passed' => $passed,
            'detail' => $slug,
        ];

        return [
            'total'         => $total,
            'criteria'      => $criteria,
            'focus_keyword' => $focus_keyword,
        ];
    }

    /**
     * Extract the most frequent meaningful keyword from title and content.
     *
     * @param string $title
     * @param string $content
     * @return string
     */
    public function extract_keyword( $title, $content ) {
        $stopwords = [
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'any', 'can', 'had', 'her',
            'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new',
            'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say',
            'she', 'too', 'use', 'with', 'this', 'that', 'have', 'from', 'they', 'will', 'been',
            'said', 'each', 'what', 'which', 'their', 'time', 'more', 'very', 'when', 'come',
            'here', 'just', 'like', 'long', 'make', 'many', 'over', 'such', 'take', 'than',
            'them', 'well', 'were', 'your', 'also', 'back', 'into', 'than', 'then', 'some',
            'about', 'after', 'before', 'could', 'first', 'great', 'other', 'people', 'should',
            'there', 'these', 'think', 'those', 'through', 'where', 'while', 'would',
        ];

        $text = $title . ' ' . strip_tags( $content );
        $text = strtolower( preg_replace( '/[^a-zA-Z\s]/', ' ', $text ) );
        $words = preg_split( '/\s+/', $text );

        $freq = [];
        foreach ( $words as $word ) {
            $word = trim( $word );
            if ( strlen( $word ) < 4 ) {
                continue;
            }
            if ( in_array( $word, $stopwords, true ) ) {
                continue;
            }
            $freq[ $word ] = ( $freq[ $word ] ?? 0 ) + 1;
        }

        arsort( $freq );
        $top = array_keys( array_slice( $freq, 0, 1 ) );

        return $top[0] ?? '';
    }

    /**
     * Count words in HTML content.
     *
     * @param string $html
     * @return int
     */
    public function word_count( $html ) {
        $text = strip_tags( $html );
        $text = trim( preg_replace( '/\s+/', ' ', $text ) );
        if ( empty( $text ) ) {
            return 0;
        }
        return str_word_count( $text );
    }

    /**
     * Get meta description for a post (Yoast or fallback).
     *
     * @param int $post_id
     * @return string
     */
    public function get_meta_desc( $post_id ) {
        $desc = get_post_meta( $post_id, '_yoast_wpseo_metadesc', true );
        if ( empty( $desc ) ) {
            $desc = get_post_meta( $post_id, '_insight_seo_metadesc', true );
        }
        return (string) $desc;
    }
}
