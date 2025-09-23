-- Fix missing emails for typeform bQ0CoIjB using CORRECT column: input_json_as_is
-- The issue was using answers_json instead of input_json_as_is

-- STEP 1: Test query to see what we can extract (SAFE - read only)
SELECT 
    typeform_form_id,
    candidate_email as current_email,
    input_json_as_is->'hidden'->>'email' as hidden_email,
    input_json_as_is->>'email' as direct_email,
    CASE 
        WHEN candidate_email IS NULL OR candidate_email = '' OR TRIM(candidate_email) = ''
        THEN 'NEEDS_FIX'
        ELSE 'HAS_EMAIL'
    END as status,
    created_at
FROM source_cloud_functions.typeform_responses
WHERE typeform_form_id = 'bQ0CoIjB'
ORDER BY created_at DESC
LIMIT 10;

-- STEP 2: Count how many records we can fix
SELECT 
    COUNT(*) as total_records,
    COUNT(CASE WHEN candidate_email IS NULL OR candidate_email = '' OR TRIM(candidate_email) = '' 
          THEN 1 END) as missing_emails,
    COUNT(CASE WHEN input_json_as_is->'hidden'->>'email' IS NOT NULL 
          THEN 1 END) as has_hidden_email,
    COUNT(CASE WHEN (candidate_email IS NULL OR candidate_email = '' OR TRIM(candidate_email) = '')
                AND input_json_as_is->'hidden'->>'email' IS NOT NULL
          THEN 1 END) as fixable_records
FROM source_cloud_functions.typeform_responses
WHERE typeform_form_id = 'bQ0CoIjB';

-- STEP 3: THE ACTUAL UPDATE (uncomment to run)
-- ⚠️ This will modify data - make sure steps 1 & 2 look correct first!

/*
UPDATE source_cloud_functions.typeform_responses
SET candidate_email = COALESCE(
    -- Try hidden fields first (most reliable for Typeform)
    input_json_as_is->'hidden'->>'email',
    input_json_as_is->'hidden'->>'Email',
    input_json_as_is->'hidden'->>'EMAIL',
    
    -- Try direct field access
    input_json_as_is->>'email',
    input_json_as_is->>'Email', 
    input_json_as_is->>'EMAIL',
    
    -- Fallback to nested list structure
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
    
    -- Final fallback: empty string
    ''
)
WHERE typeform_form_id = 'bQ0CoIjB'
  AND COALESCE(TRIM(candidate_email), '') = ''  -- Handles NULL, empty, and whitespace
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
  );
*/

-- STEP 4: Verify results after update
/*
SELECT 
    COUNT(*) as total_records,
    COUNT(CASE WHEN candidate_email IS NULL OR candidate_email = '' OR TRIM(candidate_email) = '' 
          THEN 1 END) as still_missing,
    COUNT(CASE WHEN candidate_email IS NOT NULL AND candidate_email != '' AND TRIM(candidate_email) != '' 
          THEN 1 END) as now_has_email
FROM source_cloud_functions.typeform_responses
WHERE typeform_form_id = 'bQ0CoIjB';
*/
