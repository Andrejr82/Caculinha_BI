import { z } from 'zod';

const looseStringSchema = z.union([z.string(), z.number()]).transform(String);
const looseBooleanSchema = z.union([z.boolean(), z.number(), z.string()]).transform((value) => {
  if (typeof value === 'boolean') return value;
  if (typeof value === 'number') return value !== 0;
  return ['true', '1', 'yes', 'sim', 'done'].includes(value.trim().toLowerCase());
});
const looseNumberSchema = z.union([z.number(), z.string()]).transform((value) => Number(value));
const citationSchema = z.record(z.string(), z.unknown());

const imageAssetSchema = z.object({
  url: looseStringSchema.pipe(z.string().min(1)),
  alt: looseStringSchema.optional(),
  prompt: looseStringSchema.optional(),
}).passthrough();

const audioAssetSchema = z.object({
  url: looseStringSchema.pipe(z.string().min(1)),
  title: looseStringSchema.optional(),
  mime_type: looseStringSchema.optional(),
}).passthrough();

const automationArtifactSchema = z.object({
  filename: looseStringSchema.optional(),
  download_url: looseStringSchema.optional(),
  mime_type: looseStringSchema.optional(),
  size_bytes: looseNumberSchema.optional(),
}).passthrough();

const automationDraftSchema = z.object({
  channel: looseStringSchema.optional(),
  recipient: looseStringSchema.optional(),
  subject: looseStringSchema.optional(),
  body: looseStringSchema.optional(),
}).passthrough();

const automationStateSchema = z.object({
  proposal_id: looseStringSchema.optional(),
  approval_id: looseStringSchema.optional(),
  approval_status: looseStringSchema.optional(),
  action: looseStringSchema.optional(),
  title: looseStringSchema.optional(),
  summary: looseStringSchema.optional(),
  request_text: looseStringSchema.optional(),
  params: z.record(z.string(), z.unknown()).optional(),
  target_label: looseStringSchema.optional(),
  review_required: looseBooleanSchema.optional(),
  follow_up_action: looseStringSchema.optional(),
  follow_up_label: looseStringSchema.optional(),
  result_summary: looseStringSchema.optional(),
  execution_error: looseStringSchema.optional(),
  artifact: automationArtifactSchema.optional(),
  draft: automationDraftSchema.optional(),
}).passthrough();

const dashboardSpecSchema = z.object({
  title: looseStringSchema.optional(),
  filters: z.record(z.string(), z.unknown()).optional(),
  widgets: z.array(z.record(z.string(), z.unknown())).optional(),
}).passthrough();

const chartSpecSchema = z.union([
  z.object({
    data: z.array(z.unknown()).optional(),
    layout: z.record(z.string(), z.unknown()).optional(),
  }).passthrough(),
  z.record(z.string(), z.unknown()),
]);

const tableRowSchema = z.record(z.string(), z.unknown());

export const streamEventPayloadSchema = z.object({
  type: looseStringSchema.optional(),
  text: looseStringSchema.optional(),
  done: looseBooleanSchema.optional(),
  error: looseStringSchema.optional(),
  request_id: looseStringSchema.optional(),
  source: looseStringSchema.optional(),
  mode: looseStringSchema.optional(),
  confidence: looseNumberSchema.optional(),
  citations: z.array(citationSchema).optional(),
  chart_spec: chartSpecSchema.optional(),
  chart_data: z.union([chartSpecSchema, z.string()]).optional(),
  table_data: z.array(tableRowSchema).optional(),
  data: z.array(tableRowSchema).optional(),
  dashboard_spec: dashboardSpecSchema.optional(),
  image_asset: z.union([imageAssetSchema, z.string()]).optional(),
  audio_asset: z.union([audioAssetSchema, z.string()]).optional(),
  automation_request: automationStateSchema.optional(),
}).passthrough();

export type StreamEventPayload = z.infer<typeof streamEventPayloadSchema>;

export const safeParseStreamEventPayload = (rawValue: unknown): StreamEventPayload | null => {
  const parsed = streamEventPayloadSchema.safeParse(rawValue);
  return parsed.success ? parsed.data : null;
};

export const safeParseDashboardSpec = (rawValue: unknown) => {
  const parsed = dashboardSpecSchema.safeParse(rawValue);
  return parsed.success ? parsed.data : undefined;
};

export const safeParseChartSpec = (rawValue: unknown) => {
  const parsed = chartSpecSchema.safeParse(rawValue);
  return parsed.success ? parsed.data : undefined;
};

export const safeParseTableData = (rawValue: unknown) => {
  const parsed = z.array(tableRowSchema).safeParse(rawValue);
  return parsed.success && parsed.data.length > 0 ? parsed.data : undefined;
};

export const safeParseImageAsset = (rawValue: unknown) => {
  const parsed = imageAssetSchema.safeParse(rawValue);
  return parsed.success ? parsed.data : undefined;
};

export const safeParseAudioAsset = (rawValue: unknown) => {
  const parsed = audioAssetSchema.safeParse(rawValue);
  return parsed.success ? parsed.data : undefined;
};

export const safeParseAutomationState = (rawValue: unknown) => {
  const parsed = automationStateSchema.safeParse(rawValue);
  return parsed.success ? parsed.data : undefined;
};

export const safeParseCitations = (rawValue: unknown) => {
  const parsed = z.array(citationSchema).safeParse(rawValue);
  return parsed.success ? parsed.data : [];
};
