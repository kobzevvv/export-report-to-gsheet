-- Fix Future Data Ingestions: Ensure new typeform responses extract emails correctly
-- This provides multiple approaches to handle future data

-- =============================================================================
-- APPROACH 1: DATABASE TRIGGER (Recommended)
-- =============================================================================
-- This automatically fixes candidate_email when new records are inserted/updated

CREATE OR REPLACE FUNCTION fix_candidate_email_on_insert()
RETURNS TRIGGER AS $$
BEGIN
    -- Only process if candidate_email is empty and we have JSON data
    IF (NEW.candidate_email IS NULL OR NEW.candidate_email = '' OR TRIM(NEW.candidate_email) = '') 
       AND NEW.input_json_as_is IS NOT NULL THEN
        
        -- Extract email using the enhanced logic
        NEW.candidate_email := COALESCE(
            -- Strategy 1: Hidden fields (PRIMARY for Typeform)
            NEW.input_json_as_is->'hidden'->>'email',
            NEW.input_json_as_is->'hidden'->>'Email',
            NEW.input_json_as_is->'hidden'->>'EMAIL',
            
            -- Strategy 2: Direct field access
            NEW.input_json_as_is->>'email',
            NEW.input_json_as_is->>'Email',
            NEW.input_json_as_is->>'EMAIL',
            
            -- Strategy 3: Nested list structure (existing logic)
            (
                SELECT COALESCE(
                    item->>'value_text',
                    item->>'answer',
                    item->>'text',
                    item->>'value'
                )
                FROM jsonb_array_elements(
                    CASE
                        WHEN NEW.input_json_as_is ? 'list' AND jsonb_typeof(NEW.input_json_as_is->'list') = 'array'
                        THEN NEW.input_json_as_is->'list'
                        ELSE '[]'::jsonb
                    END
                ) item
                WHERE LOWER(item->>'question_title') LIKE '%email%'
                   OR LOWER(item->>'title') LIKE '%email%'
                   OR LOWER(item->>'question') LIKE '%email%'
                   OR LOWER(item->>'name') LIKE '%email%'
                LIMIT 1
            ),
            
            -- Strategy 4: Email pattern matching
            (
                SELECT value_text
                FROM jsonb_each_text(NEW.input_json_as_is) 
                WHERE value_text ~* '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                LIMIT 1
            ),
            
            -- Keep empty if nothing found
            ''
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the trigger
DROP TRIGGER IF EXISTS trigger_fix_candidate_email ON source_cloud_functions.typeform_responses;
CREATE TRIGGER trigger_fix_candidate_email
    BEFORE INSERT OR UPDATE ON source_cloud_functions.typeform_responses
    FOR EACH ROW
    EXECUTE FUNCTION fix_candidate_email_on_insert();

-- =============================================================================
-- APPROACH 2: SCHEDULED JOB (Alternative)
-- =============================================================================
-- Run this periodically (e.g., every hour) to catch any missed emails

-- Create a function to fix recent records
CREATE OR REPLACE FUNCTION fix_recent_typeform_emails()
RETURNS TABLE(
    fixed_count INTEGER,
    total_processed INTEGER
) AS $$
DECLARE
    fixed_count INTEGER := 0;
    total_processed INTEGER := 0;
BEGIN
    -- Fix records from the last 24 hours where candidate_email is empty
    UPDATE source_cloud_functions.typeform_responses
    SET candidate_email = COALESCE(
        -- Strategy 1: Hidden fields (PRIMARY)
        input_json_as_is->'hidden'->>'email',
        input_json_as_is->'hidden'->>'Email',
        input_json_as_is->'hidden'->>'EMAIL',
        
        -- Strategy 2: Direct field access
        input_json_as_is->>'email',
        input_json_as_is->>'Email',
        input_json_as_is->>'EMAIL',
        
        -- Strategy 3: Nested list structure
        (
            SELECT COALESCE(
                item->>'value_text',
                item->>'answer',
                item->>'text',
                item->>'value'
            )
            FROM jsonb_array_elements(
                CASE
                    WHEN input_json_as_is ? 'list' AND jsonb_typeof(input_json_as_is->'list') = 'array'
                    THEN input_json_as_is->'list'
                    ELSE '[]'::jsonb
                END
            ) item
            WHERE LOWER(item->>'question_title') LIKE '%email%'
               OR LOWER(item->>'title') LIKE '%email%'
               OR LOWER(item->>'question') LIKE '%email%'
               OR LOWER(item->>'name') LIKE '%email%'
            LIMIT 1
        ),
        
        -- Strategy 4: Email pattern matching
        (
            SELECT value_text
            FROM jsonb_each_text(input_json_as_is) 
            WHERE value_text ~* '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            LIMIT 1
        ),
        
        ''
    )
    WHERE created_at > NOW() - INTERVAL '24 hours'
      AND COALESCE(TRIM(candidate_email), '') = ''
      AND input_json_as_is IS NOT NULL
      AND (
          input_json_as_is->'hidden'->>'email' IS NOT NULL
          OR input_json_as_is->>'email' IS NOT NULL
          OR EXISTS (
              SELECT 1 
              FROM jsonb_array_elements(
                  CASE
                      WHEN input_json_as_is ? 'list' AND jsonb_typeof(input_json_as_is->'list') = 'array'
                      THEN input_json_as_is->'list'
                      ELSE '[]'::jsonb
                  END
              ) item
              WHERE LOWER(item->>'question_title') LIKE '%email%'
          )
          OR EXISTS (
              SELECT 1
              FROM jsonb_each_text(input_json_as_is) 
              WHERE value_text ~* '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
          )
      );
    
    GET DIAGNOSTICS fixed_count = ROW_COUNT;
    
    -- Count total records processed in the last 24 hours
    SELECT COUNT(*) INTO total_processed
    FROM source_cloud_functions.typeform_responses
    WHERE created_at > NOW() - INTERVAL '24 hours';
    
    RETURN QUERY SELECT fix_recent_typeform_emails.fixed_count, fix_recent_typeform_emails.total_processed;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- APPROACH 3: MANUAL BATCH FIX (For immediate use)
-- =============================================================================
-- Fix ALL typeform IDs where emails are missing (not just one specific ID)

-- Count how many records need fixing across all typeforms
SELECT 
    'Summary across all typeforms' as summary,
    COUNT(*) as total_records,
    COUNT(CASE WHEN COALESCE(TRIM(candidate_email), '') = '' THEN 1 END) as missing_emails,
    COUNT(CASE WHEN input_json_as_is->'hidden'->>'email' IS NOT NULL THEN 1 END) as has_hidden_email,
    COUNT(CASE WHEN COALESCE(TRIM(candidate_email), '') = '' 
                AND input_json_as_is->'hidden'->>'email' IS NOT NULL THEN 1 END) as fixable_records
FROM source_cloud_functions.typeform_responses;

-- Show breakdown by typeform_form_id
SELECT 
    typeform_form_id,
    COUNT(*) as total_records,
    COUNT(CASE WHEN COALESCE(TRIM(candidate_email), '') = '' THEN 1 END) as missing_emails,
    COUNT(CASE WHEN input_json_as_is->'hidden'->>'email' IS NOT NULL THEN 1 END) as has_hidden_email,
    COUNT(CASE WHEN COALESCE(TRIM(candidate_email), '') = '' 
                AND input_json_as_is->'hidden'->>'email' IS NOT NULL THEN 1 END) as fixable_records
FROM source_cloud_functions.typeform_responses
GROUP BY typeform_form_id
HAVING COUNT(CASE WHEN COALESCE(TRIM(candidate_email), '') = '' THEN 1 END) > 0
ORDER BY fixable_records DESC;

-- =============================================================================
-- BATCH UPDATE FOR ALL TYPEFORMS (Uncomment to run)
-- =============================================================================
/*
UPDATE source_cloud_functions.typeform_responses
SET candidate_email = COALESCE(
    -- Strategy 1: Hidden fields (PRIMARY)
    input_json_as_is->'hidden'->>'email',
    input_json_as_is->'hidden'->>'Email',
    input_json_as_is->'hidden'->>'EMAIL',
    
    -- Strategy 2: Direct field access
    input_json_as_is->>'email',
    input_json_as_is->>'Email',
    input_json_as_is->>'EMAIL',
    
    -- Strategy 3: Nested list structure
    (
        SELECT COALESCE(
            item->>'value_text',
            item->>'answer',
            item->>'text',
            item->>'value'
        )
        FROM jsonb_array_elements(
            CASE
                WHEN input_json_as_is ? 'list' AND jsonb_typeof(input_json_as_is->'list') = 'array'
                THEN input_json_as_is->'list'
                ELSE '[]'::jsonb
            END
        ) item
        WHERE LOWER(item->>'question_title') LIKE '%email%'
           OR LOWER(item->>'title') LIKE '%email%'
           OR LOWER(item->>'question') LIKE '%email%'
           OR LOWER(item->>'name') LIKE '%email%'
        LIMIT 1
    ),
    
    -- Strategy 4: Email pattern matching
    (
        SELECT value_text
        FROM jsonb_each_text(input_json_as_is) 
        WHERE value_text ~* '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        LIMIT 1
    ),
    
    ''
)
WHERE COALESCE(TRIM(candidate_email), '') = ''  -- Only fix empty emails
  AND input_json_as_is IS NOT NULL
  AND (
      input_json_as_is->'hidden'->>'email' IS NOT NULL
      OR input_json_as_is->>'email' IS NOT NULL
      OR EXISTS (
          SELECT 1 
          FROM jsonb_array_elements(
              CASE
                  WHEN input_json_as_is ? 'list' AND jsonb_typeof(input_json_as_is->'list') = 'array'
                  THEN input_json_as_is->'list'
                  ELSE '[]'::jsonb
              END
          ) item
          WHERE LOWER(item->>'question_title') LIKE '%email%'
      )
      OR EXISTS (
          SELECT 1
          FROM jsonb_each_text(input_json_as_is) 
          WHERE value_text ~* '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
      )
  );
*/

-- =============================================================================
-- MONITORING QUERIES
-- =============================================================================

-- Daily health check - run this regularly
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_responses,
    COUNT(CASE WHEN COALESCE(TRIM(candidate_email), '') = '' THEN 1 END) as missing_emails,
    ROUND(
        COUNT(CASE WHEN COALESCE(TRIM(candidate_email), '') = '' THEN 1 END) * 100.0 / COUNT(*), 
        2
    ) as percent_missing
FROM source_cloud_functions.typeform_responses
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Show recent records that still need fixing
SELECT 
    typeform_form_id,
    candidate_email,
    input_json_as_is->'hidden'->>'email' as hidden_email_available,
    created_at
FROM source_cloud_functions.typeform_responses
WHERE COALESCE(TRIM(candidate_email), '') = ''
  AND input_json_as_is->'hidden'->>'email' IS NOT NULL
  AND created_at > NOW() - INTERVAL '1 day'
ORDER BY created_at DESC
LIMIT 10;
