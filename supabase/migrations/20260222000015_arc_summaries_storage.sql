-- M19: Arc Summaries Supabase Storage bucket
-- Stores cached Gemini arc summaries as JSON blobs (private — VIP Max only)

INSERT INTO storage.buckets (id, name, public)
VALUES ('arc-summaries', 'arc-summaries', false)
ON CONFLICT DO NOTHING;

-- Authenticated users can read (service role writes via backend)
CREATE POLICY "arc_summaries_read" ON storage.objects
    FOR SELECT USING (bucket_id = 'arc-summaries' AND auth.role() = 'authenticated');
