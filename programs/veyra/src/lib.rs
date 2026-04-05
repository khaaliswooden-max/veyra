use anchor_lang::prelude::*;

declare_id!("VeYra55mBdZFvgFjSJGnmVZWe2FsBM3VN47L6PemxGWy");

// ─── Events ────────────────────────────────────────────────────────────────

#[event]
pub struct ReasoningComplete {
    pub request_id: String,
    pub context: String,
    pub v_score: u8,
    pub latency_ms: u32,
    pub output_hash: [u8; 32],
    pub timestamp: i64,
}

// ─── Accounts ──────────────────────────────────────────────────────────────

#[account]
pub struct ReasoningRecord {
    pub authority: Pubkey,
    pub request_id: String,    // max 64 bytes
    pub context: String,       // max 128 bytes
    pub v_score: u8,
    pub latency_ms: u32,
    pub output_hash: [u8; 32],
    pub status: String,        // "PENDING" | "COMPLETE"
    pub timestamp: i64,
    pub bump: u8,
}

impl ReasoningRecord {
    pub const LEN: usize = 8 + 32 + (4 + 64) + (4 + 128) + 1 + 4 + 32 + (4 + 8) + 8 + 1;
}

// ─── Error codes ───────────────────────────────────────────────────────────

#[error_code]
pub enum VeyraError {
    #[msg("Request ID must not be empty")]
    EmptyRequestId,
    #[msg("V-Score must be between 0 and 100")]
    InvalidVScore,
    #[msg("Unauthorized: signer is not the record authority")]
    Unauthorized,
    #[msg("Reasoning request is not pending")]
    NotPending,
}

// ─── Program ───────────────────────────────────────────────────────────────

#[program]
pub mod veyra {
    use super::*;

    /// Submit a new reasoning request (from ZWM causal trigger or direct call).
    pub fn submit_reasoning(
        ctx: Context<SubmitReasoning>,
        request_id: String,
        context: String,
    ) -> Result<()> {
        require!(!request_id.is_empty(), VeyraError::EmptyRequestId);

        let record = &mut ctx.accounts.reasoning_record;
        let clock = Clock::get()?;

        record.authority = ctx.accounts.authority.key();
        record.request_id = request_id;
        record.context = context;
        record.v_score = 0;
        record.latency_ms = 0;
        record.output_hash = [0u8; 32];
        record.status = "PENDING".to_string();
        record.timestamp = clock.unix_timestamp;
        record.bump = ctx.bumps.reasoning_record;

        Ok(())
    }

    /// Complete a reasoning request, recording the result.
    /// Emits ReasoningComplete so the ZWM indexer records the SubstrateEvent.
    pub fn complete_reasoning(
        ctx: Context<CompleteReasoning>,
        v_score: u8,
        latency_ms: u32,
        output_hash: [u8; 32],
    ) -> Result<()> {
        require!(v_score <= 100, VeyraError::InvalidVScore);

        let record = &mut ctx.accounts.reasoning_record;
        require!(record.authority == ctx.accounts.authority.key(), VeyraError::Unauthorized);
        require!(record.status == "PENDING", VeyraError::NotPending);

        let clock = Clock::get()?;
        let request_id = record.request_id.clone();
        let context = record.context.clone();

        record.v_score = v_score;
        record.latency_ms = latency_ms;
        record.output_hash = output_hash;
        record.status = "COMPLETE".to_string();
        record.timestamp = clock.unix_timestamp;

        emit!(ReasoningComplete {
            request_id,
            context,
            v_score,
            latency_ms,
            output_hash,
            timestamp: clock.unix_timestamp,
        });

        Ok(())
    }
}

// ─── Instruction Contexts ──────────────────────────────────────────────────

#[derive(Accounts)]
#[instruction(request_id: String)]
pub struct SubmitReasoning<'info> {
    #[account(
        init,
        payer = authority,
        space = ReasoningRecord::LEN,
        seeds = [b"reasoning", request_id.as_bytes()],
        bump,
    )]
    pub reasoning_record: Account<'info, ReasoningRecord>,

    #[account(mut)]
    pub authority: Signer<'info>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct CompleteReasoning<'info> {
    #[account(
        mut,
        seeds = [b"reasoning", reasoning_record.request_id.as_bytes()],
        bump = reasoning_record.bump,
    )]
    pub reasoning_record: Account<'info, ReasoningRecord>,

    pub authority: Signer<'info>,
}
