CREATE TABLE `proofpay_events` (
	`id` text PRIMARY KEY NOT NULL,
	`workspace_id` text NOT NULL,
	`operation_id` text,
	`type` text NOT NULL,
	`detail` text NOT NULL,
	`created_at` integer NOT NULL,
	FOREIGN KEY (`workspace_id`) REFERENCES `proofpay_workspaces`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `proofpay_event_workspace` ON `proofpay_events` (`workspace_id`);--> statement-breakpoint
CREATE TABLE `proofpay_operations` (
	`id` text PRIMARY KEY NOT NULL,
	`workspace_id` text NOT NULL,
	`idempotency_key` text NOT NULL,
	`request` text NOT NULL,
	`agent_label` text NOT NULL,
	`sku` text NOT NULL,
	`title` text NOT NULL,
	`amount_cents` integer NOT NULL,
	`currency` text NOT NULL,
	`merchant_id` text NOT NULL,
	`mode` text NOT NULL,
	`ai_source` text NOT NULL,
	`rationale` text NOT NULL,
	`status` text NOT NULL,
	`approval_version` integer DEFAULT 1 NOT NULL,
	`approval_expires_at` integer,
	`approval_digest` text,
	`create_request_id` text NOT NULL,
	`capture_request_id` text NOT NULL,
	`order_id` text,
	`capture_id` text,
	`approval_url` text,
	`created_at` integer NOT NULL,
	`updated_at` integer NOT NULL,
	FOREIGN KEY (`workspace_id`) REFERENCES `proofpay_workspaces`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE UNIQUE INDEX `proofpay_operations_create_request_id_unique` ON `proofpay_operations` (`create_request_id`);--> statement-breakpoint
CREATE UNIQUE INDEX `proofpay_operations_capture_request_id_unique` ON `proofpay_operations` (`capture_request_id`);--> statement-breakpoint
CREATE UNIQUE INDEX `proofpay_operations_order_id_unique` ON `proofpay_operations` (`order_id`);--> statement-breakpoint
CREATE UNIQUE INDEX `proofpay_operations_capture_id_unique` ON `proofpay_operations` (`capture_id`);--> statement-breakpoint
CREATE UNIQUE INDEX `proofpay_operation_idempotency` ON `proofpay_operations` (`workspace_id`,`idempotency_key`);--> statement-breakpoint
CREATE INDEX `proofpay_operation_workspace` ON `proofpay_operations` (`workspace_id`);--> statement-breakpoint
CREATE TABLE `proofpay_rehearsal_orders` (
	`id` text PRIMARY KEY NOT NULL,
	`operation_id` text NOT NULL,
	`payload` text NOT NULL,
	`capture_calls` integer DEFAULT 0 NOT NULL,
	`created_at` integer NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `proofpay_rehearsal_orders_operation_id_unique` ON `proofpay_rehearsal_orders` (`operation_id`);--> statement-breakpoint
CREATE TABLE `proofpay_sessions` (
	`owner_id` text PRIMARY KEY NOT NULL,
	`workspace_id` text NOT NULL,
	FOREIGN KEY (`workspace_id`) REFERENCES `proofpay_workspaces`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `proofpay_workspaces` (
	`id` text PRIMARY KEY NOT NULL,
	`owner_id` text NOT NULL,
	`mode` text NOT NULL,
	`currency` text NOT NULL,
	`budget_cents` integer NOT NULL,
	`created_at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `proofpay_workspace_owner` ON `proofpay_workspaces` (`owner_id`);