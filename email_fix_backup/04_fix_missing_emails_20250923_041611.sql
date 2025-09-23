-- Generated on 2025-09-23 04:16:11
-- Typeform Email Extraction Fix
-- Table: source_cloud_functions.typeform_responses


        -- UPDATE Query: Fix missing candidate emails
        -- This query will update records where candidate_email is empty but email can be extracted
        
        UPDATE source_cloud_functions.typeform_responses
        SET 
            candidate_email = (
                
        COALESCE(
            -- Strategy 1: Hidden fields (PRIMARY for Typeform responses)
            answers_json->'hidden'->>'email',
            answers_json->'hidden'->>'Email', 
            answers_json->'hidden'->>'EMAIL',
            answers_json->'hidden'->>'e-mail',
            answers_json->'hidden'->>'E-mail',
            
            -- Strategy 2: Direct field access
            answers_json->>'email',
            answers_json->>'Email',
            answers_json->>'EMAIL',
            answers_json->>'e-mail',
            answers_json->>'E-mail',
            
            -- Strategy 3: Nested list structure (existing pattern)
            (
                SELECT COALESCE(
                    item->>'value_text',
                    item->>'answer', 
                    item->>'text',
                    item->>'value',
                    item->>'response'
                )
                FROM jsonb_array_elements(
                    CASE
                        WHEN answers_json ? 'list' AND jsonb_typeof(answers_json->'list') = 'array'
                        THEN answers_json->'list'
                        ELSE '[]'::jsonb
                    END
                ) item
                WHERE LOWER(item->>'question_title') LIKE '%email%'
                   OR LOWER(item->>'title') LIKE '%email%'
                   OR LOWER(item->>'question') LIKE '%email%'
                   OR LOWER(item->>'name') LIKE '%email%'
                   OR LOWER(item->>'field_title') LIKE '%email%'
                LIMIT 1
            ),
            
            -- Strategy 4: Array search with email pattern matching
            (
                SELECT COALESCE(
                    elem->>'value_text',
                    elem->>'value',
                    elem->>'text', 
                    elem->>'answer',
                    elem->>'response'
                )
                FROM jsonb_array_elements(
                    CASE
                        WHEN jsonb_typeof(answers_json) = 'array'
                        THEN answers_json
                        ELSE jsonb_build_array(answers_json)
                    END
                ) elem
                WHERE (elem->>'value_text')::text ~* '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                   OR (elem->>'value')::text ~* '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                   OR (elem->>'text')::text ~* '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                   OR (elem->>'answer')::text ~* '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                LIMIT 1
            ),
            
            -- Strategy 5: Deep search in any nested structure
            (
                SELECT value_text
                FROM jsonb_each_text(answers_json) 
                WHERE value_text ~* '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                LIMIT 1
            ),
            
            -- Fallback: empty string
            ''
        )
            ),
            updated_at = CURRENT_TIMESTAMP  -- Update timestamp if column exists
        WHERE 
            -- Only update records where candidate_email is missing/empty
            (candidate_email IS NULL OR candidate_email = '' OR TRIM(candidate_email) = '')
            
            -- And where we can actually extract an email
            AND answers_json IS NOT NULL
            AND (
                -- Check if email exists in any of these locations
                answers_json->'hidden'->>'email' IS NOT NULL
                OR answers_json->>'email' IS NOT NULL
                OR EXISTS (
                    SELECT 1 
                    FROM jsonb_array_elements(
                        CASE
                            WHEN answers_json ? 'list' AND jsonb_typeof(answers_json->'list') = 'array'
                            THEN answers_json->'list'
                            ELSE '[]'::jsonb
                        END
                    ) item
                    WHERE LOWER(item->>'question_title') LIKE '%email%'
                       OR (item->>'value_text')::text ~* '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                )
                OR EXISTS (
                    SELECT 1
                    FROM jsonb_each_text(answers_json) 
                    WHERE value ~* '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                )
            );
        