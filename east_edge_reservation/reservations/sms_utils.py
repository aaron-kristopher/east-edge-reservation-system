import requests
import logging
import math

logger = logging.getLogger(__name__)


# --- Formal SMS Segmentation Function (v3 - Word Boundary, Suffix: - Part x of y, Extra Debug) ---
def segment_formal_sms(
    body_content: str, recipient_name: str, sender_name: str, limit: int = 160
) -> list[str]:
    logger.debug(
        "--- Starting FORMAL SMS Segmentation (v3 - Word Boundary, Suffix: - Part x of y) ---"
    )
    logger.debug(
        f"Recipient: '{recipient_name}', Sender: '{sender_name}', Limit: {limit}"
    )
    logger.debug(
        f"Body Content (first 100): '{body_content[:100]}...' (Len: {len(body_content)})"
    )

    if not recipient_name or not sender_name:
        logger.error("Recipient and Sender names are required for formal segmentation.")
        return []

    intro = f"Dear {recipient_name},\n\n"
    outro = f"\n\nKindly yours,\n{sender_name}"
    ellipsis_str = "..."
    ellipsis_len = len(ellipsis_str)

    if not body_content.strip():
        logger.debug("Body content is empty.")
        single_segment_with_intro_outro = intro + outro.strip()
        suffix_one_part = " - Part 1 of 1"
        if len(single_segment_with_intro_outro + suffix_one_part) <= limit:
            final_msg = single_segment_with_intro_outro + suffix_one_part
            logger.debug(
                f"Empty body, sending intro/outro: '{final_msg}' (Len: {len(final_msg)})"
            )
            return [final_msg]
        else:
            logger.error("Empty body, and intro + outro + suffix exceeds limit.")
            return []

    estimated_total_parts = 0
    body_parts_data = []

    for estimation_pass in range(2):
        temp_body_parts_data_this_pass = []
        current_body_ptr = 0
        part_num_estimation = 0
        temp_needs_leading_ellipsis_for_next = False

        logger.debug(f"Starting estimation pass {estimation_pass + 1}")

        while current_body_ptr < len(body_content) or \
              (part_num_estimation == 0 and estimation_pass == 0):

            part_num_estimation += 1
            logger.debug(f"  Estimating part {part_num_estimation}, current_body_ptr: {current_body_ptr}")
            estimated_suffix_len = 20 # For "- Part XX of YY"
            
            available_chars_for_body_content = limit - estimated_suffix_len
            
            current_part_leading_ellipsis = temp_needs_leading_ellipsis_for_next
            temp_needs_leading_ellipsis_for_next = False

            is_first_part_estimation = (len(temp_body_parts_data_this_pass) == 0)

            if is_first_part_estimation:
                available_chars_for_body_content -= len(intro)
            if current_part_leading_ellipsis:
                available_chars_for_body_content -= ellipsis_len
            
            # Tentative outro reservation (estimation only)
            if current_body_ptr + available_chars_for_body_content >= len(body_content):
                 if not temp_needs_leading_ellipsis_for_next:
                    available_chars_for_body_content -= len(outro)

            if available_chars_for_body_content < 0: available_chars_for_body_content = 0
            logger.debug(f"    Available for body content (estimation): {available_chars_for_body_content}")

            body_chunk_taken = ""
            chars_advanced_in_body = 0
            current_part_trailing_ellipsis = False

            remaining_body_at_ptr = body_content[current_body_ptr:]
            logger.debug(f"    Remaining body at ptr (first 50): '{remaining_body_at_ptr[:50]}...'")


            if not remaining_body_at_ptr.strip():
                logger.debug(f"    No more actual body content at ptr {current_body_ptr}.")
                if current_part_leading_ellipsis:
                     logger.debug(f"      Part {part_num_estimation} will be leading ellipsis and possibly outro.")
                     body_chunk_taken = ""
                     chars_advanced_in_body = 0 # No actual body characters consumed
                else:
                    if len(temp_body_parts_data_this_pass) > 0:
                        logger.debug("      No leading ellipsis and no body, ending estimation loop for this pass.")
                        break 
                    else:
                        logger.debug("      First part estimation, no body content (should be caught by initial check).")
                        pass # Should have been caught by initial empty body_content check
            else:
                sentence_enders = ['.', '?', '!']
                first_hard_stop_idx_in_remaining = -1
                for i_rem, char_rem in enumerate(remaining_body_at_ptr):
                    if char_rem in sentence_enders:
                        is_true_hard_stop = False
                        if (i_rem + 1 == len(remaining_body_at_ptr)): is_true_hard_stop = True
                        elif (i_rem + 1 < len(remaining_body_at_ptr)):
                            next_char = remaining_body_at_ptr[i_rem+1]
                            if next_char == ' ': is_true_hard_stop = True
                            elif 'A' <= next_char <= 'Z': is_true_hard_stop = True
                            elif next_char == '\n': is_true_hard_stop = True
                        if is_true_hard_stop:
                            first_hard_stop_idx_in_remaining = i_rem
                            break
                
                logger.debug(f"    First hard stop in remaining: {first_hard_stop_idx_in_remaining}")
                if first_hard_stop_idx_in_remaining != -1:
                    text_to_hard_stop = remaining_body_at_ptr[:first_hard_stop_idx_in_remaining + 1]
                    logger.debug(f"    Text to hard stop (len {len(text_to_hard_stop)}): '{text_to_hard_stop[:50]}...'")
                    if len(text_to_hard_stop) <= available_chars_for_body_content:
                        body_chunk_taken = text_to_hard_stop
                        chars_advanced_in_body = len(text_to_hard_stop)
                        logger.debug("      Took full sentence to hard stop.")
                    else: # Sentence (to hard stop) is too long. Apply Rule 3 (ellipsis).
                        logger.debug(f"      Sentence to hard stop too long for available space {available_chars_for_body_content}.")
                        if available_chars_for_body_content > ellipsis_len:
                            potential_ellipsis_chunk = remaining_body_at_ptr[:available_chars_for_body_content - ellipsis_len]
                            space_idx = potential_ellipsis_chunk.rfind(' ')
                            if space_idx > 0 :
                                body_chunk_taken = potential_ellipsis_chunk[:space_idx]
                                chars_advanced_in_body = space_idx + 1
                            elif space_idx == 0 and len(potential_ellipsis_chunk) > 0 :
                                body_chunk_taken = ""
                                chars_advanced_in_body = 1
                            else:
                                body_chunk_taken = potential_ellipsis_chunk
                                chars_advanced_in_body = len(potential_ellipsis_chunk)
                            current_part_trailing_ellipsis = True
                            temp_needs_leading_ellipsis_for_next = True
                            logger.debug(f"        Applied ellipsis (word boundary). Chunk: '{body_chunk_taken[:50]}...'")
                        else:
                            body_chunk_taken = remaining_body_at_ptr[:available_chars_for_body_content]
                            chars_advanced_in_body = len(body_chunk_taken)
                            if chars_advanced_in_body < len(remaining_body_at_ptr) and chars_advanced_in_body > 0:
                                current_part_trailing_ellipsis = True
                                temp_needs_leading_ellipsis_for_next = True
                            logger.debug(f"        Applied ellipsis (no space for full ellipsis_str, hard break). Chunk: '{body_chunk_taken[:50]}...'")
                else: # No hard stop in remaining body. The rest is one chunk.
                    logger.debug("    No hard stop in remaining body.")
                    if len(remaining_body_at_ptr) <= available_chars_for_body_content:
                        body_chunk_taken = remaining_body_at_ptr
                        chars_advanced_in_body = len(remaining_body_at_ptr)
                        logger.debug("      Took all remaining (no hard stop).")
                    else: # Remaining part is too long, must break with ellipsis.
                        logger.debug(f"      Remaining body too long for available space {available_chars_for_body_content}.")
                        if available_chars_for_body_content > ellipsis_len:
                            potential_ellipsis_chunk = remaining_body_at_ptr[:available_chars_for_body_content - ellipsis_len]
                            space_idx = potential_ellipsis_chunk.rfind(' ')
                            if space_idx > 0:
                                body_chunk_taken = potential_ellipsis_chunk[:space_idx]
                                chars_advanced_in_body = space_idx + 1
                            elif space_idx == 0 and len(potential_ellipsis_chunk) > 0 :
                                body_chunk_taken = ""
                                chars_advanced_in_body = 1
                            else:
                                body_chunk_taken = potential_ellipsis_chunk
                                chars_advanced_in_body = len(potential_ellipsis_chunk)
                            current_part_trailing_ellipsis = True
                            temp_needs_leading_ellipsis_for_next = True
                            logger.debug(f"        Applied ellipsis (word boundary). Chunk: '{body_chunk_taken[:50]}...'")
                        else:
                            body_chunk_taken = remaining_body_at_ptr[:available_chars_for_body_content]
                            chars_advanced_in_body = len(body_chunk_taken)
                            if chars_advanced_in_body < len(remaining_body_at_ptr) and chars_advanced_in_body > 0:
                                current_part_trailing_ellipsis = True
                                temp_needs_leading_ellipsis_for_next = True
                            logger.debug(f"        Applied ellipsis (no space for full ellipsis_str, hard break). Chunk: '{body_chunk_taken[:50]}...'")
            
            logger.debug(f"    Body chunk taken (len {len(body_chunk_taken.strip())}, original advance {chars_advanced_in_body}): '{body_chunk_taken.strip()[:50]}...'")
            current_body_ptr += chars_advanced_in_body
            logger.debug(f"    New current_body_ptr: {current_body_ptr}. Trailing ellipsis: {current_part_trailing_ellipsis}. Needs leading for next: {temp_needs_leading_ellipsis_for_next}")

            temp_body_parts_data_this_pass.append({
                "body_text": body_chunk_taken.strip(),
                "needs_leading_ellipsis": current_part_leading_ellipsis,
                "needs_trailing_ellipsis": current_part_trailing_ellipsis
            })
            
            if current_body_ptr >= len(body_content) and not temp_needs_leading_ellipsis_for_next:
                logger.debug("    End of body reached and no pending ellipsis for next. Breaking estimation inner loop.")
                break

        body_parts_data = temp_body_parts_data_this_pass
        if estimated_total_parts == len(temp_body_parts_data_this_pass) and estimated_total_parts > 0:
            logger.debug(f"Formal segmentation part count stabilized at {estimated_total_parts} parts after pass {estimation_pass+1}.")
            break
        else:
            estimated_total_parts = len(temp_body_parts_data_this_pass)
            if estimated_total_parts == 0 and len(body_content) > 0: estimated_total_parts = 1
            logger.debug(f"Formal segmentation pass {estimation_pass+1} finished. New estimated_total_parts: {estimated_total_parts}")
            if estimation_pass == 1 and (not body_parts_data or estimated_total_parts != len(body_parts_data)):
                 logger.warning(f"Formal part count did NOT stabilize. Using {estimated_total_parts}. Body parts count: {len(body_parts_data)}")

    actual_final_segments = []
    if not body_parts_data and body_content.strip():
        logger.error("Formal segmentation loop failed to produce body parts data for non-empty body.")
        return [intro + body_content.strip()[:limit-len(intro)-len(outro)-20-ellipsis_len] + ellipsis_str + outro + " - Part 1 of 1 ERROR"]

    total_final_parts = len(body_parts_data)
    if total_final_parts == 0:
        logger.info("No body parts data to segment (likely empty initial body), returning empty list.")
        return []

    for i, segment_data in enumerate(body_parts_data):
        part_num = i + 1
        is_first_segment = (part_num == 1)
        is_last_segment = (part_num == total_final_parts)
        
        suffix = f" - Part {part_num} of {total_final_parts}"
        
        current_segment_text = ""
        
        if is_first_segment:
            current_segment_text += intro
        
        if segment_data["needs_leading_ellipsis"]:
            current_segment_text += ellipsis_str
            
        current_segment_text += segment_data["body_text"]
        
        if segment_data["needs_trailing_ellipsis"]:
            current_segment_text += ellipsis_str
            
        if is_last_segment and not segment_data["needs_trailing_ellipsis"]:
            temp_stripped = current_segment_text.rstrip('\n')
            current_segment_text = temp_stripped
            current_segment_text += outro

        final_text_for_segment = current_segment_text.strip() + suffix
        
        if len(final_text_for_segment) > limit:
            logger.warning(
                f"Segment {part_num}/{total_final_parts} is OVERSIZED ({len(final_text_for_segment)} > {limit}). "
                f"Content before suffix: '{current_segment_text.strip().replace(chr(10), '/n')[:80]}...'. "
                "This may be due to prioritizing hard stops or indivisible long words/sentences combined with intro/outro."
            )
        
        actual_final_segments.append(final_text_for_segment)
        logger.debug(f"Final Segment {part_num}/{total_final_parts} (Len: {len(final_text_for_segment)}): '{final_text_for_segment.replace(chr(10), '/n')[:80]}...'")

    # Final consistency check
    logger.debug(f"FINAL CHECK before returning from segment_formal_sms: Total segments generated: {len(actual_final_segments)}. Expected based on body_parts_data: {total_final_parts}")
    if len(actual_final_segments) != total_final_parts and total_final_parts > 0 : # Check total_final_parts > 0 because it could be 0 for empty body
        logger.error(f"MISMATCH! body_parts_data had {total_final_parts} items, but actual_final_segments has {len(actual_final_segments)}.")
        logger.debug("body_parts_data content:")
        for i_d, d_item in enumerate(body_parts_data): # Renamed 'd' to 'd_item'
            logger.debug(f"  Item {i_d}: {d_item}")


    logger.debug(
        "--- FORMAL SMS Segmentation FINISHED (v3 - Word Boundary, Suffix: - Part x of y) ---"
    )
    return actual_final_segments


# --- Your existing simple segmenter (segment_sms_message) ---
def segment_sms_message(message: str, limit: int = 150) -> list[str]:
    if not message:
        return []
    single_part_suffix = " (1/1)"
    if len(message) + len(single_part_suffix) <= limit:
        return [message + single_part_suffix]
    final_segments = []
    avg_suffix_len_estimation = 7
    if limit <= avg_suffix_len_estimation:
        logger.error(
            f"SIMPLE: SMS limit {limit} too small for content and suffix (avg {avg_suffix_len_estimation})."
        )
        return [message]
    content_per_part_estimation = limit - avg_suffix_len_estimation
    if content_per_part_estimation <= 0:
        content_per_part_estimation = 1
    current_total_parts_estimate = math.ceil(
        len(message) / content_per_part_estimation
    )
    if current_total_parts_estimate == 0:
        current_total_parts_estimate = 1
    for _iteration in range(5):
        segments_this_iteration = []
        msg_ptr = 0
        part_num_counter = 0
        while msg_ptr < len(message):
            part_num_counter += 1
            suffix = f" ({part_num_counter}/{current_total_parts_estimate})"
            available_for_content = limit - len(suffix)
            if available_for_content < 0:
                available_for_content = 0
            end_of_potential_slice = msg_ptr + available_for_content
            chunk_to_consider = message[
                msg_ptr : min(end_of_potential_slice, len(message))
            ]
            content_for_this_part = ""
            len_taken_from_original = 0
            if end_of_potential_slice >= len(message) or msg_ptr + len(
                chunk_to_consider
            ) >= len(message):
                content_for_this_part = message[msg_ptr:]
                len_taken_from_original = len(content_for_this_part)
            else:
                newline_idx_rel = chunk_to_consider.rfind("\n")
                space_idx_rel = chunk_to_consider.rfind(" ")
                if newline_idx_rel != -1:
                    content_for_this_part = chunk_to_consider[: newline_idx_rel + 1]
                    len_taken_from_original = newline_idx_rel + 1
                elif space_idx_rel != -1: 
                    if space_idx_rel > 0: 
                        content_for_this_part = chunk_to_consider[:space_idx_rel]
                        len_taken_from_original = space_idx_rel + 1 
                    elif space_idx_rel == 0 and len(chunk_to_consider) > 0: 
                        content_for_this_part = "" 
                        len_taken_from_original = 1 
                    else: 
                        content_for_this_part = chunk_to_consider
                        len_taken_from_original = len(chunk_to_consider)
                else:
                    content_for_this_part = chunk_to_consider
                    len_taken_from_original = len(chunk_to_consider)

            if len_taken_from_original == 0 and msg_ptr < len(message):
                if available_for_content > 0:
                    len_taken_from_original = min(
                        available_for_content, len(message) - msg_ptr
                    )
                    content_for_this_part = message[
                        msg_ptr : msg_ptr + len_taken_from_original
                    ]
                else:
                    segments_this_iteration.append(
                        f"ErrorSimplePart{part_num_counter}{suffix}"
                    )
                    msg_ptr = len(message)
                    continue
            segments_this_iteration.append(content_for_this_part.strip() + suffix)
            msg_ptr += len_taken_from_original
        final_segments = segments_this_iteration
        if part_num_counter == current_total_parts_estimate:
            break
        else:
            current_total_parts_estimate = part_num_counter
            if current_total_parts_estimate == 0 and len(message) > 0:
                current_total_parts_estimate = 1
            if _iteration == 4:
                logger.warning(
                    "SIMPLE: SMS segmentation for total_parts did not stabilize."
                )
    for i, seg_content in enumerate(final_segments):
        if len(seg_content) > limit:
            logger.error(
                f"SIMPLE: Segment {i+1} is too long ({len(seg_content)} chars, limit {limit})."
            )
    return final_segments


# --- send_sms and send_reservation_sms (Copied from your prompt) ---
try:
    from django.conf import settings 
except ImportError:
    settings = None 
    logger.warning("Django 'settings' not imported. SMS sending will be simulated or fail if not mocked.")

def send_sms(
    phone_number: str,
    message_body_content: str,
    recipient_name: str,
    sender_name: str,
    sms_char_limit: int = 160,
    use_formal_segmenter: bool = True,
) -> bool:
    
    TRACCAR_SMS_GATEWAY_URL_val = None
    TRACCAR_SMS_API_KEY_val = None

    if settings: 
        TRACCAR_SMS_GATEWAY_URL_val = getattr(settings, "TRACCAR_SMS_GATEWAY_URL", None)
        TRACCAR_SMS_API_KEY_val = getattr(settings, "TRACCAR_SMS_API_KEY", None)
        if not TRACCAR_SMS_GATEWAY_URL_val:
            logger.error("TRACCAR_SMS_GATEWAY_URL is not configured in settings.")
            return False
        if not TRACCAR_SMS_API_KEY_val:
            logger.error("TRACCAR_SMS_API_KEY is not configured in settings.")
            return False
    elif not use_formal_segmenter: 
        logger.warning("Django settings not available, TRACCAR checks skipped for simple segmenter test.")
    else: 
        logger.error("Django settings not available. Cannot proceed with formal SMS send without TRACCAR_SMS_GATEWAY_URL and TRACCAR_SMS_API_KEY.")
        return False


    if not phone_number:
        logger.warning("Attempted to send SMS but no phone number was provided.")
        return False
    if not message_body_content.strip() and use_formal_segmenter:
        pass
    elif not message_body_content.strip():
        logger.info(f"Empty message body provided for {phone_number}, no SMS sent.")
        return True

    normalized_phone_number = phone_number
    if phone_number.startswith("09") and len(phone_number) == 11:
        normalized_phone_number = "+639" + phone_number[2:]
    elif phone_number.startswith("+639") and len(phone_number) == 13:
        normalized_phone_number = phone_number
    else:
        logger.warning(
            f"Phone number {phone_number} format not recognized for normalization. Sending as is."
        )
    
    api_key_to_use = TRACCAR_SMS_API_KEY_val if settings else "MOCK_API_KEY_FOR_STANDALONE"
    gateway_url_to_use = TRACCAR_SMS_GATEWAY_URL_val if settings else "http://mock.url.example.com"


    headers = {
        "Content-Type": "application/json",
        "Authorization": api_key_to_use,
    }
    segments: list[str] = []

    if use_formal_segmenter:
        logger.info(f"Using FORMAL segmenter for SMS to {normalized_phone_number}.")
        segments = segment_formal_sms(
            message_body_content, recipient_name, sender_name, limit=sms_char_limit
        )
    else:
        logger.info(f"Using SIMPLE segmenter for SMS to {normalized_phone_number}.")
        segments = segment_sms_message(
            message_body_content, limit=sms_char_limit
        )

    if not segments and message_body_content.strip():
        logger.error(
            f"SMS segmentation failed for {normalized_phone_number} (produced no segments): '{message_body_content[:50]}...'"
        )
        return False
    if not segments:
        logger.info(
            f"No segments to send for {normalized_phone_number} after segmentation."
        )
        return True

    all_parts_successful = True
    logger.info(
        f"SEGMENTER produced {len(segments)} segments for {normalized_phone_number}." # Added log
    )
    for idx, seg_text_log in enumerate(segments): # Added log
        logger.debug(f"  Segment content to send {idx+1}/{len(segments)} (len: {len(seg_text_log)}): '{seg_text_log.replace(chr(10),'/n')}'")

    for i, part_message in enumerate(segments):
        payload = {"to": normalized_phone_number, "message": part_message}
        try:
            logger.debug(
                f"  Attempting to send part {i+1}/{len(segments)} (len: {len(part_message)}): '{part_message.replace(chr(10),'/n')}'"
            )
            if not settings: 
                print(f"    [SIMULATED SEND to {gateway_url_to_use}] PAYLOAD: {payload}")
                continue 

            response = requests.post(
                gateway_url_to_use,
                json=payload,
                headers=headers,
                timeout=20,
            )
            response.raise_for_status()
            logger.info(
                f"  SMS part {i+1}/{len(segments)} for {normalized_phone_number} accepted. Status: {response.status_code}."
            )
        except Exception as e:
            logger.error(
                f"  ERROR sending part {i+1}/{len(segments)} to {normalized_phone_number}: {e}"
            )
            all_parts_successful = False
            break
    return all_parts_successful


def send_reservation_sms(
    customer_phone_number: str,
    barber_phone_number: str,
    customer_message_body: str,
    barber_message_body: str,
    customer_recipient_name: str,
    barber_recipient_name: str,
    company_sender_name: str,
):
    customer_success = False
    if customer_phone_number and customer_message_body.strip():
        logger.info(f"Sending reservation SMS to customer {customer_phone_number}")
        customer_success = send_sms(
            customer_phone_number,
            customer_message_body,
            customer_recipient_name,
            company_sender_name,
            use_formal_segmenter=True,
        )
    else:
        logger.debug("Skipping customer SMS: No phone or message body.")

    barber_success = False
    if barber_phone_number and barber_message_body.strip():
        logger.info(f"Sending reservation SMS to barber {barber_phone_number}")
        barber_success = send_sms(
            barber_phone_number,
            barber_message_body,
            barber_recipient_name,
            company_sender_name,
            use_formal_segmenter=True,
        )
    else:
        logger.debug("Skipping barber SMS: No phone or message body.")
    return customer_success and barber_success

def send_cancellation_sms(
        phone_number: str,
        message_body: str,
        recipient_name: str,
        sender_name: str
):
    cancellation_sms_success = False

    if phone_number and message_body.strip():
        logger.info(f"Sending reservation SMS to customer {phone_number}")
        cancellation_sms_success = send_sms(
            phone_number,
            message_body,
            recipient_name,
            sender_name,
            use_formal_segmenter=True,
        )
    else:
        logger.debug("Skipping customer SMS: No phone or message body.")

    return cancellation_sms_success
